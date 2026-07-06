import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bmi_history.db')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise e

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

def add_user(name):
    if not name or not name.strip():
        return None
    name = name.strip()
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # User already exists
    except sqlite3.Error as e:
        print(f"Database error adding user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY name ASC")
        rows = cursor.fetchall()
        return [{'id': row['id'], 'name': row['name']} for row in rows]
    except sqlite3.Error as e:
        print(f"Database error fetching users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_record(user_id, weight, height, bmi):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO records (user_id, weight, height, bmi) VALUES (?, ?, ?, ?)",
            (user_id, weight, height, bmi)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding BMI record: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_records(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM records 
            WHERE user_id = ? 
            ORDER BY timestamp ASC
        ''', (user_id,))
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            records.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'weight': row['weight'],
                'height': row['height'],
                'bmi': row['bmi'],
                'timestamp': row['timestamp']
            })
        return records
    except sqlite3.Error as e:
        print(f"Database error fetching BMI records: {e}")
        return []
    finally:
        if conn:
            conn.close()
