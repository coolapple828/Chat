# tutor.py
from flask import Blueprint, render_template, request, session, redirect, url_for
import openai

from db_utils import is_subscribed
# Use your OpenAI key or local model
openai.api_key = "sk-..."  # Replace with your key

tutor_bp = Blueprint('tutor', __name__)

@tutor_bp.route("/tutor", methods=["GET", "POST"])
def tutor():
    if "username" not in session:
        return redirect(url_for("signin"))
    
    username = session['username']
    if not is_subscribed(username, "aiweb"):
        return "Access denied: You are not subscribed to AI Web Builder."

    question = ""
    answer = ""

    if request.method == "POST":
        question = request.form.get("question", "")
        if question:
            # Using OpenAI GPT to respond
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You're a helpful tutor for students."},
                        {"role": "user", "content": question}
                    ]
                )
                answer = response['choices'][0]['message']['content']
            except Exception as e:
                answer = f"Error: {str(e)}"

    return render_template("tutor.html", question=question, answer=answer)
