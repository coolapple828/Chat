from flask import Flask, render_template, request, redirect, session, url_for
import stripe
import os
import sqlite3 as db
from auth import auth_bp
from stripe_routes import stripe_bp
from db_utils import init_db
from admin import admin_bp
from tutor import tutor_bp
from user import user_bp  # adjust this import path
from aiweb import aiweb_bp








app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Init DB
init_db()

# Register Blueprints
app.register_blueprint(aiweb_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(stripe_bp)
app.register_blueprint(tutor_bp)
app.register_blueprint(user_bp)


@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
