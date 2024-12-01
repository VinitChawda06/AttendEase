import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from config import DATABASE_NAME

def init_auth_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def create_user(username, password, role):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, hashed_password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def login(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[2], password):
        return {"id": user[0], "username": user[1], "role": user[3]}
    return None

def check_user_role(username, required_role):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username = ?", (username,))
    user_role = c.fetchone()
    conn.close()
    
    if user_role and user_role[0] == required_role:
        return True
    return False

def get_all_users():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users")
    users = [{"id": row[0], "username": row[1], "role": row[2]} for row in c.fetchall()]
    conn.close()
    return users