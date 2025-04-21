import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

# Initialize users and subscriptions tables
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            username TEXT UNIQUE,
            password TEXT,
            date_joined TEXT,
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'user'
        )
    ''')
        # Create subscriptions table for multiple service premiums
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                service_name TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                UNIQUE(username, service_name)
            )
        ''')

        conn.commit()

# Add a regular user
def add_user(fullname, username, password):
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (fullname, username, password, date_joined, is_active, role)
                VALUES (?, ?, ?, ?, 1, 'user')
            ''', (fullname, username, password, now))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

# Add an admin user
def add_admin(fullname, username, password):
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (fullname, username, password, date_joined, is_active, role)
                VALUES (?, ?, ?, ?, 1, 'admin')
            ''', (fullname, username, password, now))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

# Check if user is premium for a specific service
def is_subscribed(username, service_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT is_premium FROM subscriptions 
            WHERE username = ? AND service_name = ?
        ''', (username, service_name))
        result = cursor.fetchone()
        return result and result[0] == 1

# Update or create a user's premium status for a service
def update_user_premium(username, service_name, is_premium):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO subscriptions (username, service_name, is_premium)
            VALUES (?, ?, ?)
            ON CONFLICT(username, service_name)
            DO UPDATE SET is_premium=excluded.is_premium
        ''', (username, service_name, is_premium))
        conn.commit()

# Check if a user exists
def user_exists(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone() is not None

# Validate username and password
def validate_login(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        return cursor.fetchone() is not None

# Get full name
def get_fullname(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT fullname FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else None

# Get full user record by username
def get_user(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

# Check if the user is an admin
def is_admin(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        return user and user[0] == 'admin'

# Run on import
init_db()

# Seed test users
if not user_exists('admin1'):
    add_admin('Test Admin', 'admin1', 'adminpass')

if not user_exists('testuser'):
    add_user('Test User', 'testuser', 'userpass')
    update_user_premium('testuser', 'AI_Tutor', 1)
    update_user_premium('testuser', 'Website_Builder', 1)
