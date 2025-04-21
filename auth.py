from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3 as db
import datetime as dt
from db_utils import get_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)

        if user and user['password'] == password and user['is_active']:
            session['username'] = username
            session['is_admin'] = False
            return redirect(url_for('home'))
        else:
            return "Invalid credentials or account inactive"
    return render_template('signin.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        free_expires = (dt.datetime.now() + dt.timedelta(days=3)).strftime('%Y-%m-%d')

        conn = db.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO users (fullname, username, password, date_joined, is_active, role)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
               (fullname, username, password, now, 1, 'user'))
            cursor.execute('''INSERT INTO subscriptions (username, service_name, is_premium)
                  VALUES (?, ?, ?)''', (username, '0', 0))
            conn.commit()
        except db.IntegrityError:
            return "Username already exists."
        except db.OperationalError:
            return "Database error. Please try again."
        finally:
            conn.close()

        return redirect(url_for('auth.signin'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))
