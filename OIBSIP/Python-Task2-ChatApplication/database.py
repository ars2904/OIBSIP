import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert a default general room if it doesn't exist
    try:
        cursor.execute("INSERT OR IGNORE INTO rooms (name) VALUES (?)", ("General",))
    except sqlite3.Error as e:
        print(f"Error creating default room: {e}")
        
    conn.commit()
    conn.close()

def register_user(username, password):
    if not username or not password:
        return None
    
    username = username.strip()
    password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None  # Username already exists
    finally:
        conn.close()

def verify_user(username, password):
    if not username or not password:
        return None
    
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return {
            'id': user['id'],
            'username': user['username']
        }
    return None

def create_room(room_name, created_by_user_id):
    if not room_name:
        return None
    
    room_name = room_name.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO rooms (name, created_by) VALUES (?, ?)",
            (room_name, created_by_user_id)
        )
        conn.commit()
        room_id = cursor.lastrowid
        return room_id
    except sqlite3.IntegrityError:
        return None  # Room name already exists
    finally:
        conn.close()

def get_rooms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms ORDER BY name ASC")
    rooms = cursor.fetchall()
    conn.close()
    return [{'id': r['id'], 'name': r['name']} for r in rooms]

def get_room_by_name(room_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms WHERE name = ?", (room_name,))
    room = cursor.fetchone()
    conn.close()
    if room:
        return {'id': room['id'], 'name': room['name']}
    return None

def save_message(room_name, username, message_content):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find room_id
        cursor.execute("SELECT id FROM rooms WHERE name = ?", (room_name,))
        room = cursor.fetchone()
        if not room:
            return False
        
        # Find user_id
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            return False
            
        cursor.execute(
            "INSERT INTO messages (room_id, user_id, message) VALUES (?, ?, ?)",
            (room['id'], user['id'], message_content)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error saving message: {e}")
        return False
    finally:
        conn.close()

def get_message_history(room_name, limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.message, m.timestamp, u.username 
        FROM messages m
        JOIN users u ON m.user_id = u.id
        JOIN rooms r ON m.room_id = r.id
        WHERE r.name = ?
        ORDER BY m.timestamp ASC
        LIMIT ?
    ''', (room_name, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            'username': r['username'],
            'message': r['message'],
            'timestamp': r['timestamp']
        })
    return history
