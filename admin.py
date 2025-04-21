from flask import Blueprint, request, render_template, redirect, session, url_for
import sqlite3 as db
from db_utils import is_admin

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        secret_code = request.form['secret_code']

        conn = db.connect("users.db")
        conn.row_factory = db.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cur.fetchone()
        conn.close()

        if admin and admin['password'] == password and admin['secret_code'] == secret_code:
            session['username'] = username
            session['is_admin'] = True
            return redirect(url_for('admin_bp.dashboard'))
        else:
            return "Invalid admin credentials"

    return render_template('admin_login.html')

@admin_bp.route('/admin/dashboard')
def dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))
    
    if session.get('is_admin') == False:
        return redirect(url_for('admin.admin_login'))
    
    conn = db.connect("users.db")
    conn.row_factory = db.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    conn.close()

    return render_template('admin_panel.html', users=users)

@admin_bp.route('/admin/deactivate/<username>')
def deactivate_user(username):
    if not session.get('is_admin'):
        return redirect(url_for('admin_bp.admin_login'))

    conn = db.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_bp.dashboard'))
