# aiweb.py

from flask import Blueprint, render_template, request, session, redirect, url_for
import openai
from db_utils import is_subscribed

aiweb_bp = Blueprint('aiweb', __name__, template_folder='templates')

openai.api_key = "your-openai-api-key"  # Replace with your actual API key

@aiweb_bp.route('/aiweb', methods=['GET', 'POST'])
def aiweb():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    username = session['username']
    if not is_subscribed(username, "aiweb"):
        return "Access denied: You are not subscribed to AI Web Builder."

    website_code = None
    if request.method == 'POST':
        prompt = request.form['description']
        full_prompt = f"Build a complete responsive HTML website based on this idea: '{prompt}'"

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=1500,
            temperature=0.7
        )
        website_code = response['choices'][0]['text']

    return render_template('aiweb.html', website_code=website_code)
