from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import database
import secrets
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(24)

# Initialize Flask-SocketIO with standard async_mode (will use simple-websocket if installed)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory mapping of active socket sessions: { sid: { username: "Alice", current_room: "General" } }
active_connections = {}

# Initialize database
database.init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        user = database.verify_user(username, password)
        if user:
            session['username'] = user['username']
            session['user_id'] = user['id']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid username or password'})
        
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters long'})
    if not password or len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
        
    user_id = database.register_user(username, password)
    if user_id:
        session['username'] = username
        session['user_id'] = user_id
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Username is already taken'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    rooms = database.get_rooms()
    return jsonify({'success': True, 'rooms': rooms})

@app.route('/api/rooms/create', methods=['POST'])
def create_room():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    room_name = data.get('room_name', '').strip()
    
    if not room_name or len(room_name) < 2:
        return jsonify({'success': False, 'message': 'Room name must be at least 2 characters long'})
        
    room_id = database.create_room(room_name, session['user_id'])
    if room_id:
        # Notify all connected clients about the new room
        socketio.emit('room_created', {'id': room_id, 'name': room_name})
        return jsonify({'success': True, 'room': {'id': room_id, 'name': room_name}})
    return jsonify({'success': False, 'message': 'Room name already exists'})


# --- Socket.IO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if not username:
        return False  # Reject connection
    
    active_connections[request.sid] = {
        'username': username,
        'current_room': None
    }

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in active_connections:
        user_info = active_connections[sid]
        username = user_info['username']
        current_room = user_info['current_room']
        
        if current_room:
            # Notify members in the room
            timestamp = datetime.now().strftime('%H:%M')
            emit('message', {
                'username': 'System',
                'message': f"{username} has left the chat.",
                'timestamp': timestamp,
                'is_system': True
            # pyrefly: ignore [unexpected-keyword]
            }, room=current_room)
            
        del active_connections[sid]

@socketio.on('join')
def handle_join(data):
    sid = request.sid
    if sid not in active_connections:
        return
        
    username = active_connections[sid]['username']
    room_name = data.get('room')
    
    if not room_name:
        return
        
    # Check if the room exists
    room = database.get_room_by_name(room_name)
    if not room:
        emit('error_message', {'message': 'Room does not exist'})
        return
        
    # Leave current room if any
    old_room = active_connections[sid]['current_room']
    if old_room:
        leave_room(old_room)
        timestamp = datetime.now().strftime('%H:%M')
        emit('message', {
            'username': 'System',
            'message': f"{username} has left the room.",
            'timestamp': timestamp,
            'is_system': True
        # pyrefly: ignore [unexpected-keyword]
        }, room=old_room)
        
    # Join new room
    join_room(room_name)
    active_connections[sid]['current_room'] = room_name
    
    # Load and send message history
    history = database.get_message_history(room_name)
    formatted_history = []
    for msg in history:
        # SQLite stored timestamp could be raw string. We will parse it to format if needed, 
        # but let's parse or use as is. The database inserts CURRENT_TIMESTAMP. 
        # Let's extract hour and minute for the chat window.
        try:
            # SQLite format: YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S')
            ts = dt.strftime('%H:%M')
        except Exception:
            ts = datetime.now().strftime('%H:%M') # Fallback
            
        formatted_history.append({
            'username': msg['username'],
            'message': msg['message'],
            'timestamp': ts,
            'is_system': False
        })
        
    emit('history', {'room': room_name, 'messages': formatted_history})
    
    # Notify other users in the room
    timestamp = datetime.now().strftime('%H:%M')
    emit('message', {
        'username': 'System',
        'message': f"{username} has joined the room.",
        'timestamp': timestamp,
        'is_system': True
    # pyrefly: ignore [unexpected-keyword]
    }, room=room_name, include_self=False)

@socketio.on('leave')
def handle_leave(data):
    sid = request.sid
    if sid not in active_connections:
        return
        
    username = active_connections[sid]['username']
    room_name = data.get('room')
    
    if room_name and active_connections[sid]['current_room'] == room_name:
        leave_room(room_name)
        active_connections[sid]['current_room'] = None
        timestamp = datetime.now().strftime('%H:%M')
        emit('message', {
            'username': 'System',
            'message': f"{username} has left the room.",
            'timestamp': timestamp,
            'is_system': True
        # pyrefly: ignore [unexpected-keyword]
        }, room=room_name)

@socketio.on('send_message')
def handle_send_message(data):
    sid = request.sid
    if sid not in active_connections:
        return
        
    user_info = active_connections[sid]
    username = user_info['username']
    room_name = user_info['current_room']
    message_content = data.get('message', '').strip()
    
    if not room_name or not message_content:
        return
        
    # Save message to database
    database.save_message(room_name, username, message_content)
    
    # Broadcast to the room
    timestamp = datetime.now().strftime('%H:%M')
    emit('message', {
        'username': username,
        'message': message_content,
        'timestamp': timestamp,
        'is_system': False
    # pyrefly: ignore [unexpected-keyword]
    }, room=room_name)

@socketio.on('typing')
def handle_typing(data):
    sid = request.sid
    if sid not in active_connections:
        return
        
    user_info = active_connections[sid]
    username = user_info['username']
    room_name = user_info['current_room']
    is_typing = data.get('is_typing', False)
    
    if room_name:
        emit('typing_status', {
            'username': username,
            'is_typing': is_typing
        # pyrefly: ignore [unexpected-keyword]
        }, room=room_name, include_self=False)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
