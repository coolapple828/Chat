from flask import Blueprint, session, redirect, url_for, render_template, request
import stripe
import sqlite3
from db_utils import update_user_premium

stripe_bp = Blueprint('stripe_bp', __name__)

stripe.api_key = 'sk_test_your_secret_key'
STRIPE_PUBLIC_KEY = 'pk_test_your_public_key'
MONTHLY_PRICE_ID = 'price_1234567890abcdef'
SERVICES = ['AI_Tutor', 'Website_Builder', 'Recipe_Generator', 'Travel_Planner']

def get_user_services(username):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT service_name, is_premium FROM subscriptions WHERE username=?", (username,))
        data = cursor.fetchall()
        conn.close()
        return {service: bool(status) for service, status in data}
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return {}

@stripe_bp.route('/subscriptions', methods=['GET', 'POST'])
def manage_subscriptions():
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        service = request.form.get('service')
        action = request.form.get('action')

        if not service or not action:
            return "Missing service or action", 400

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()

            if action == 'subscribe':
                cursor.execute("REPLACE INTO subscriptions (username, service_name, is_premium) VALUES (?, ?, ?)",
                               (username, service, 1))
            elif action == 'unsubscribe':
                cursor.execute("UPDATE subscriptions SET is_premium=? WHERE username=? AND service_name=?",
                               (0, username, service))

            conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
            return "An error occurred while updating the subscription.", 500
        finally:
            conn.close()

        return redirect(url_for('stripe_bp.manage_subscriptions'))

    services = get_user_services(username)
    return render_template('subs.html', services=services, available_services=SERVICES, public_key=STRIPE_PUBLIC_KEY)

@stripe_bp.route('/subscribe')
def subscribe():
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.signin'))

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price': MONTHLY_PRICE_ID, 'quantity': 1}],
        mode='subscription',
        success_url=url_for('stripe_bp.success', _external=True),
        cancel_url=url_for('stripe_bp.cancel', _external=True),
        metadata={'username': username}
    )
    session['checkout_session_id'] = checkout_session.id

    return redirect(checkout_session.url, code=303)

@stripe_bp.route('/success')
def success():
    username = session.get('username')
    if username:
        update_user_premium(username)
    return "Subscription successful. Premium access granted!"

@stripe_bp.route('/cancel')
def cancel():
    return "Subscription canceled."
