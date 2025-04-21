from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3

user_bp = Blueprint('user', __name__)

@user_bp.route('/user')
def user_page():
    if 'username' not in session:
        return redirect(url_for('auth.login'))  # or whatever your login route is

    username = session['username']

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, date_joined FROM users WHERE username = ?", (username,))
    cursor.execute("SELECT is_premium FROM subscriptions WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        fullname, date_joined, is_premium = result
        return render_template("user.html", username=fullname, date_joined=date_joined, premium=is_premium)
    else:
        return "User not found", 404
