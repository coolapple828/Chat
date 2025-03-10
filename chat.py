import os
from flask import (
    Flask, request, render_template_string, redirect, session, 
    send_from_directory
)
from markupsafe import escape
import datetime as dt
import random, string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "my_super_secret_key"  # Required for session management

# Configure uploads folder and allowed extensions.
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

# Ensure the upload folder exists.
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# Global Data Storage
# =============================================================================
# List of posts made by users. Each post is a dict.
user_posts = []
# Counter to assign unique IDs to posts.
post_id_counter = 1

class Member:
    free_days = 365
    all_members = []  # In-memory list of members

    def __init__(self, uname, fname, password):
        self.username = uname
        self.fullname = fname
        self.password = password  # Store provided password
        self.date_joined = dt.date.today()
        self.is_active = True
        self.free_expires = dt.date.today() + dt.timedelta(days=Member.free_days)
        Member.all_members.append(self)

    def deactivate(self):
        self.is_active = False

class Admin(Member):
    # Store admin objects keyed by username.
    admins = {}

    def __init__(self, uname, fname, password, secret_code):
        super().__init__(uname, fname, password)  # Pass actual password
        self.secret_code = secret_code
        Admin.admins[uname] = self

# Create sample admin accounts.
admin1 = Admin("admin1", "Liam", "ld", "LiamIsTheBest")
admin2 = Admin("admin2", "Sophia", "SR", "SophiaRules")

# Dummy ChatMessage class (for displaying public chat messages).
class ChatMessage:
    all_messages = []
    
    def __init__(self, username, message):
        self.username = username
        self.message = message
        ChatMessage.all_messages.append(self)
    def encode(self):
        pass

# Global storage for public and private chats.
# Each message is stored as a dictionary with keys: username, message, and optional file.
public_chat_messages = []
private_chats = {}  # Dictionary mapping a 7-character code to a list of messages.

# =============================================================================
# Route: Sign In Page ("/")
# =============================================================================
@app.route("/", methods=["GET", "POST"])
def signin():
    # Example: apply your limiter here if needed.
    if session.get("username"):
        # Redirect admin users to /admin; others to /linkpage
        return redirect("/admin" if session["username"] in Admin.admins else "/linkpage")
    
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        secret_code = request.form.get("secret_code", "").strip()

        # Check if user is an admin.
        if username in Admin.admins:
            admin_obj = Admin.admins[username]
            if password == admin_obj.password:
                if secret_code == admin_obj.secret_code:
                    session["username"] = admin_obj.username
                    session["fullname"] = admin_obj.fullname
                    return redirect("/admin")
                else:
                    error = "Invalid secret code for admin."
            else:
                error = "Incorrect password."
        else:
            found_member = next((m for m in Member.all_members if m.username == username), None)
            if found_member:
                if found_member.password == password:
                    if found_member.is_active:
                        session["username"] = found_member.username
                        session["fullname"] = found_member.fullname
                        return redirect("/linkpage")
                    else:
                        error = "Access Denied. Your account has been deactivated."
                else:
                    error = "Incorrect password."
            else:
                error = "No such user found. Please register first."
    
    # Render the external HTML file "1.html" from the templates folder.
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <title>Sign In</title>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width">
      <style>
         body { background-color: #2C3E50; color: white; font-family: Arial, sans-serif; }
         .header { background-color: #34495E; padding: 20px; text-align: center; border-radius: 10px; }
         .container { text-align: center; padding: 20px; }
         input[type="text"], input[type="password"] {
             padding: 10px; margin: 5px; border-radius: 5px; border: none; font-size: 16px;
         }
         input[type="submit"] {
             background-color: #3498DB; color: white; border: none; padding: 10px 15px;
             border-radius: 5px; cursor: pointer;
         }
         input[type="submit"]:hover { background-color: #2980B9; }
         .error { color: #e74c3c; }
         a { color: #1ABC9C; text-decoration: none; }
      </style>
    </head>
    <body>
      <div class="header">
         <h1>Sign In</h1>
      </div>
      <div class="container">
         <form action="/" method="POST">
             <label for="username">Username:</label>
             <input type="text" id="username" name="username" required><br>
             <label for="password">Password:</label>
             <input type="password" id="password" name="password" required><br>
             <label for="secret_code">Secret Code (only for admins):</label>
             <input type="password" id="secret_code" name="secret_code"><br>
             <input type="submit" value="Sign In">
         </form>
         {% if error %}
            <p class="error">{{ error }}</p>
         {% endif %}
         <br>
         <a href="/register">Register</a>
      </div>
    </body>
    </html>
    """, error=error)


@app.route("/signout")
def signout():
    session.clear()
    return redirect("/")


# =============================================================================
# Route: Navigation Hub ("/linkpage")
# =============================================================================
@app.route("/linkpage")
def linkpage():
    if "username" not in session:
        return redirect("/")
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Home</title>
  <style>
    body {
      background-color: #2C3E50;
      color: white;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
    }
    
    .header {
      background-color: #34495E;
      padding: 20px;
      text-align: center;
      border-bottom: 2px solid #2980B9;
    }
    
    .topnav {
      background-color: #333;
      overflow: hidden;
      padding: 10px 0;
      text-align: center;
    }
    
    .topnav form {
      display: inline-block;
      margin: 0 5px;
    }
    
    .topnav input[type="submit"] {
      background-color: #3498DB;
      color: white;
      border: none;
      padding: 10px 15px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 17px;
    }
    
    .topnav input[type="submit"]:hover {
      background-color: #2980B9;
    }
    
    /* Optional: Style the Sign Out button differently */
    .topnav form.signout {
      margin-left: 20px;
    }
    
    .container {
      text-align: center;
      padding: 20px;
    }
    .column {
      float: left;
      text-align: center;
      padding: 10px;
    }
/* Left and right column */
    .column.side {
      text-align: center;
      width: 25%;
    }
/* Middle column */
    .column.middle {
      text-align: center;
      width: 50%;
    }
                                  
    .column form {
      display: inline-block;
      margin: 0 5px;
    }
    
    .column input[type="submit"] {
      background-color: #3498DB;
      color: white;
      border: none;
      padding: 10px 15px;
      border-radius: 5px;
      cursor: pointer;
     font-size: 17px;
    }
    
    .column [type="submit"]:hover {
       background-color: #2980B9;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Welcome, {{ session['fullname'] }}!</h1>
  </div>
  
  <div class="topnav">
    <form action="/public_chat">
      <input type="submit" value="Public Chat">
    </form>
    <form action="/videos">
      <input type="submit" value="Videos">
    </form>
  </div>
  
   <div class="column side">
    <h2> Side Bar </h2>
      <form action="/racing">
      <input type="submit" value="Racing Cars">
    </form>
    <p> </p>
    <form action="/guess">
      <input type="submit" value="Guessing Game">
    </form>
       <p> </p>
    <form action="/game">
      <input type="submit" value="Rock Paper Scissors">
    </form>
       <p> </p>
    <form action="/user">
      <input type="submit" value="Userpage">
    </form>
   <p> </p>                              
    <form action="/signout" class="signout">
      <input type="submit" value="Sign Out">
    </form>
       <p> </p>
  </div>
</body>
</html>""")

# =============================================================================
# Route: Registration
# =============================================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"].strip()
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if any(m.username == username for m in Member.all_members):
            return "<h2>Username already taken. Please choose another one.</h2>"
        new_member = Member(username, fullname, password)
        return f"<h2>Registration successful! Welcome {fullname}!</h2><a href='/'>Sign In</a>"
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <title>Register</title>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width">
      <style>
         body { background-color: #2C3E50; color: white; font-family: Arial, sans-serif; }
         .header { background-color: #34495E; padding: 20px; text-align: center; border-radius: 10px; }
         .container { text-align: center; padding: 20px; }
         input[type="text"], input[type="password"] {
             padding: 10px; margin: 5px; border-radius: 5px; border: none; font-size: 16px;
         }
         form input[type="submit"] {
             background-color: #3498DB; color: white; border: none; padding: 10px 15px;
             margin: 5px; border-radius: 5px; cursor: pointer; font-size: 16px;
         }
         form input[type="submit"]:hover { background-color: #2980B9; }
         a { color: #1ABC9C; text-decoration: none; }
      </style>
    </head>
    <body>
      <div class="header">
         <h1>Register</h1>
      </div>
      <div class="container">
         <form action="/register" method="POST">
             <label for="fullname">Full Name:</label>
             <input type="text" id="fullname" name="fullname" required><br>
             <label for="username">Username:</label>
             <input type="text" id="username" name="username" required><br>
             <label for="password">Password:</label>
             <input type="password" id="password" name="password" required><br>
             <input type="submit" value="Register">
         </form>
         <br>
         <a href="/">Sign In</a>
      </div>
    </body>
    </html>
    """)

# =============================================================================
# Route: Admin Page (Admins are sent here after sign in)
# =============================================================================
@app.route("/admin", methods=["GET", "POST"])
def admin_page():
    if "username" not in session:
        return redirect("/")
    if session["username"] not in Admin.admins:
        return redirect("/linkpage")
        
    if request.method == "POST":
        username_to_deactivate = request.form["username"].strip()
        found_member = next((m for m in Member.all_members if m.username == username_to_deactivate), None)
        if found_member:
            found_member.deactivate()
            return f"<h2>Member {found_member.fullname} has been deactivated.</h2><a href='/admin'>Back</a>"
    members_list = "<br>".join(f"Name: {m.fullname} | Username: {m.username} | Password {m.password} (Active: {m.is_active})" 
                               for m in Member.all_members)
    chat_messages = "<br>".join(f"<b>{msg.username}:</b> {msg.message}" for msg in ChatMessage.all_messages)
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Admin Panel</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width">
        <style>
            body {{
                background-color: #2C3E50;
                color: white;
                font-family: Arial, sans-serif;
            }}
            .header {{
                background-color: #34495E;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 24px;
                border-radius: 10px;
            }}
            .container {{
                padding: 20px;
                background-color: #1ABC9C;
                text-align: center;
                border-radius: 10px;
            }}
            form input[type="submit"] {{
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="header"><h1>Admin Panel</h1></div>
        <div class="container">
            <h2>All Members</h2>
            <p>{members_list}</p>
            <h2>Deactivate Member</h2>
            <form action="/admin" method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="submit" value="Deactivate">
            </form>
            <h2>Chat Messages</h2>
            <p>{chat_messages}</p>
        </div>
    </body>
    </html>
    """)

# =============================================================================
# Route: Public Chat (Updated to support file uploads)
# =============================================================================
@app.route("/public_chat", methods=["GET", "POST"])
def public_chat():
    if "username" not in session:
        return redirect("/")
    
    current_username = session["username"]
    alert_code = None
    if Member.all_members:
        random_member = random.choice(Member.all_members)
        if random_member.username == current_username:
            def generate_code():
                return ''.join(random.choices(string.ascii_letters + string.digits, k=7))
            code = generate_code()
            while code in private_chats:
                code = generate_code()
            private_chats[code] = []
            alert_code = code

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        file = request.files.get("media")
        media_filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            filename = unique_suffix + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            media_filename = filename
        if message or media_filename:
            public_chat_messages.append({
                "username": current_username,
                "message": message,
                "file": media_filename
            })
    
    # Build messages list with media rendering.
    messages_list = ""
    for msg in public_chat_messages:
        text = f"<b>{msg['username']}:</b> {msg['message']}" if msg['message'] else f"<b>{msg['username']}:</b>"
        if msg.get("file"):
            ext = msg["file"].rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                media_html = f'<br><img src="/uploads/{msg["file"]}" alt="Image" style="max-width:200px;">'
            elif ext in ['mp4', 'mov', 'avi']:
                media_html = f'<br><video width="320" height="240" controls><source src="/uploads/{msg["file"]}" type="video/{ext}">Your browser does not support the video tag.</video>'
            else:
                media_html = f'<br><a href="/uploads/{msg["file"]}">Download file</a>'
            text += media_html
        messages_list += text + "<br>"
    error = ""   
    if request.method == "POST":
        if "create" in request.form:
            def generate_code():
                return ''.join(random.choices(string.ascii_letters + string.digits, k=7))
            chat_code = generate_code()
            while chat_code in private_chats:
                chat_code = generate_code()
            private_chats[chat_code] = []
            return redirect(f"/chat/{chat_code}")
        elif "join" in request.form:
            code = request.form.get("code", "").strip()
            if code in private_chats:
                return redirect(f"/chat/{code}")
            else:
                error = "Chat room with that code does not exist."
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
         <title>Public Chat</title>
         <meta charset="UTF-8">
         <meta name="viewport" content="width=device-width">
         <style>
             body { background-color: #2C3E50; color: white; font-family: Arial, sans-serif; text-align: center; }
             .container { margin: 20px auto; padding: 20px; background-color: #34495E; border-radius: 10px; width: 50%; }
             .alert { background-color: white; color: black; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
             textarea { width: 80%; padding: 10px; margin: 10px; border-radius: 5px; }
             input[type="submit"] { background-color: #1ABC9C; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
             input[type="submit"]:hover { background-color: #16A085; }
             .chat-messages { text-align: left; margin-top: 20px; background-color: #2C3E50; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto; }
             a { color: #1ABC9C; text-decoration: none; }
         </style>
    </head>
    <body>
         <div class="container">
              {% if alert_code %}
              <div class="alert">
                   You've been randomly selected for a private chat invitation! Use this code: <strong>{{ alert_code }}</strong>
              </div>
              {% endif %}
              <h2>Public Chat Room</h2>
              <form method="POST" enctype="multipart/form-data">
                  <textarea name="message" placeholder="Type your message..."></textarea><br>
                  <input type="file" name="media"><br>
                  <input type="submit" value="Send">
              </form>
              <div class="chat-messages">
                  {{ messages_list|safe }}
              </div>
                              <h2>Private Chat</h2>
              <form method="POST">
                  <input type="submit" name="create" value="Create New Private Chat">
              </form>
              <form method="POST">
                  <input type="text" name="code" placeholder="Enter 7-character Code" required>
                  <input type="submit" name="join" value="Join Private Chat">
              </form>
              {% if error %}
                  <p class="error">{{ error }}</p>
              {% endif %}
              <br>
            <form action="/chat_manager">
            <input type="submit" value="Chat Manager">
            </form>
            <a href="/linkpage">Back to Home</a>
                        
         </div>
    </body>
    </html>
    """, alert_code=alert_code, messages_list=messages_list)

@app.route("/chat_manager")
def chat_manger():
    if "username" not in session:
        return redirect("/")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Chat Manager</title>
      <style>
        body {
          background-color: #2C3E50;
          color: white;
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
        }
        .header {
          background-color: #34495E;
          padding: 20px;
          text-align: center;
          border-bottom: 2px solid #2980B9;
        }
        .topnav {
          background-color: #333;
          overflow: hidden;
          padding: 10px 0;
          text-align: center;
        }
        .topnav form {
          display: inline-block;
          margin: 0 5px;
        }
        .topnav input[type="submit"] {
          background-color: #3498DB;
          color: white;
          border: none;
          padding: 10px 15px;
          border-radius: 5px;
          cursor: pointer;
          font-size: 17px;
        }
        .topnav input[type="submit"]:hover {
          background-color: #2980B9;
        }
        .container {
          text-align: center;
          padding: 20px;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Welcome, {{ session['fullname'] }}!</h1>
      </div>
      
      <div class="topnav">
        <form action="/public_chat">
          <input type="submit" value="Public Chat">
        </form>
        <form action="/videos">
          <input type="submit" value="Videos">
        </form>
      </div>
      
      <h2>Private Chat Codes:</h2>
      <ul>
        {% for code in private_chats %}
          <li> <a href="/chat/{{code}}">{{code}}</a> </li>
        {% endfor %}
      </ul>
    </body>
    </html>
    """, private_chats=private_chats)


# =============================================================================
# Route: Private Chat Room (Updated to support file uploads)
# =============================================================================
@app.route("/chat/<chat_code>", methods=["GET", "POST"])
def chat_room(chat_code):
    if "username" not in session:
        return redirect("/")
    if chat_code not in private_chats:
        return f"Chat room does not exist. <a href='/private_chat'>Back</a>"
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        file = request.files.get("media")
        media_filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            filename = unique_suffix + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            media_filename = filename
        if message or media_filename:
            private_chats[chat_code].append({
                "username": session["username"],
                "message": message,
                "file": media_filename
            })
    messages_list = ""
    for msg in private_chats[chat_code]:
        text = f"<b>{msg['username']}:</b> {msg['message']}" if msg['message'] else f"<b>{msg['username']}:</b>"
        if msg.get("file"):
            ext = msg["file"].rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                media_html = f'<br><img src="/uploads/{msg["file"]}" alt="Image" style="max-width:200px;">'
            elif ext in ['mp4', 'mov', 'avi']:
                media_html = f'<br><video width="320" height="240" controls><source src="/uploads/{msg["file"]}" type="video/{ext}">Your browser does not support the video tag.</video>'
            else:
                media_html = f'<br><a href="/uploads/{msg["file"]}">Download file</a>'
            text += media_html
        messages_list += text + "<br>"
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
         <title>Private Chat Room: {chat_code}</title>
         <meta charset="UTF-8">
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <style>
             body {{
                 background-color: #2C3E50;
                 color: white;
                 font-family: Arial, sans-serif;
                 text-align: center;
             }}
             .container {{
                 margin: 20px auto;
                 padding: 20px;
                 background-color: #34495E;
                 border-radius: 10px;
                 width: 50%;
             }}
             textarea {{
                 width: 80%;
                 padding: 10px;
                 margin: 10px;
                 border-radius: 5px;
             }}
             input[type="submit"] {{
                 background-color: #1ABC9C;
                 color: white;
                 border: none;
                 padding: 10px 15px;
                 border-radius: 5px;
                 cursor: pointer;
             }}
             input[type="submit"]:hover {{
                 background-color: #16A085;
             }}
             .chat-messages {{
                 text-align: left;
                 cg  
                 margin-top: 20px;
                 background-color: #2C3E50;
                 padding: 10px;
                 border-radius: 5px;
                 max-height: 300px;
                 overflow-y: auto;
             }}
             a {{ color: #1ABC9C; text-decoration: none; }}
         </style>
    </head>
    <body>
         <div class="container">
              <h2>Private Chat Room: {chat_code}</h2>
              <form method="POST" enctype="multipart/form-data">
                  <textarea name="message" placeholder="Type your message..."></textarea><br>
                  <input type="file" name="media"><br>
                  <input type="submit" value="Send">
              </form>
              <div class="chat-messages">
                  {messages_list}
              </div>
              <br>
            
            <form action="/chat_manager">
            <input type="submit" value="Chat Manager">
            </form>
         </div>
    </body>
    </html>
    """)

# =============================================================================
# Route: Serve Uploaded Files
# =============================================================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory (app.config['UPLOAD_FOLDER'], filename)


@app.route("/user", methods=["GET", "POST"])
def user():
    if "username" not in session:
        return redirect("/")
    current_username = session["username"]
    found_member = next((m for m in Member.all_members if m.username == current_username), None)
    if not found_member:
        return "User not found."
    
    message = ""
    global post_id_counter

    if request.method == "POST":
        # Update username
        if "submit_username" in request.form:
            new_username = request.form.get("newusername", "").strip()
            if new_username:
                if new_username == found_member.username:
                    message = "This is already your username."
                elif any(m.username == new_username for m in Member.all_members):
                    message = "Username already taken."
                else:
                    found_member.username = new_username
                    session["username"] = new_username
                    message = "Username updated successfully."
        # Update password
        elif "submit_password" in request.form:
            new_password = request.form.get("newpassword", "").strip()
            if new_password:
                found_member.password = new_password
                message = "Password updated successfully."
        # Create a new media post
        elif "submit_post" in request.form:
            caption = request.form.get("caption", "").strip()
            file = request.files.get("media")
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                filename = unique_suffix + "_" + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                post = {
                    "id": post_id_counter,
                    "username": current_username,
                    "caption": caption,
                    "media": filename,
                    "likes": 0,
                    "comments": []  # Each comment: {"username": ..., "comment": ...}
                }
                user_posts.append(post)
                post_id_counter += 1
                message = "Post created successfully."
            else:
                message = "Invalid file or no file uploaded."
    
    # Render the user profile with post form.
    return render_template_string("""
<html>
<head>
    <meta charset="UTF-8">
    <title>User Profile</title>
    <style>
        body { background-color: #2C3E50; color: white; font-family: Arial, sans-serif; }
        .header { background-color: #34495E; padding: 20px; text-align: center; border-radius: 10px; }
        .container { text-align: center; padding: 20px; }
        form input[type="text"], form input[type="password"], form input[type="file"] {
            padding: 10px; margin: 5px; border-radius: 5px; border: none; font-size: 16px;
        }
        form textarea {
            padding: 10px; margin: 5px; border-radius: 5px; font-size: 16px; width: 80%;
        }
        form input[type="submit"] {
            background-color: #3498DB; color: white; border: none; padding: 10px 15px;
            margin: 5px; border-radius: 5px; cursor: pointer; font-size: 16px;
        }
        form input[type="submit"]:hover { background-color: #2980B9; }
        p.message { color: yellow; }
        .post { border: 1px solid #ccc; margin: 10px auto; padding: 10px; background-color: #3C4F65; width: 80%; }
    </style>
</head>
<body>
 <div class="header">
   <h1>User Profile</h1>
 </div>
 <div class="container">
     <p><strong>Full Name:</strong> {{ fullname }}</p>
     <p><strong>Username:</strong> {{ username }}</p>
     <p><strong>Date Joined:</strong> {{ date_joined }}</p>
     {% if message %}
         <p class="message">{{ message }}</p>
     {% endif %}
     
     <h3>Change Username</h3>
     <form method="POST">
         <input type="text" name="newusername" placeholder="New Username" required>
         <input type="submit" name="submit_username" value="Change Username">
     </form>
     
     <h3>Change Password</h3>
     <form method="POST">
         <input type="password" name="newpassword" placeholder="New Password" required>
         <input type="submit" name="submit_password" value="Change Password">
     </form>
     
     <h3>Create a New Post (Image/Video)</h3>
     <form method="POST" enctype="multipart/form-data">
         <textarea name="caption" placeholder="Add a caption (optional)"></textarea><br>
         <input type="file" name="media" required><br>
         <input type="submit" name="submit_post" value="Post">
     </form>
     
     <br>
     <a href="/videos">View All Videos/Posts</a><br>
     <a href="/linkpage">Back to Home</a>
 </div>
</body>
</html>
""", fullname=found_member.fullname, username=found_member.username,
     date_joined=found_member.date_joined.strftime("%Y-%m-%d"), message=message)

# =============================================================================
# Route: Videos Page (View, Like, Comment, Search)
# =============================================================================
@app.route("/videos", methods=["GET", "POST"])
def videos():
    if "username" not in session:
        return redirect("/")
    
    # Process likes and comments.
    if request.method == "POST":
        if "like" in request.form:
            post_id = int(request.form.get("post_id"))
            for post in user_posts:
                if post["id"] == post_id:
                    post["likes"] += 1
                    break
        elif "comment" in request.form:
            post_id = int(request.form.get("post_id"))
            comment_text = request.form.get("comment", "").strip()
            if comment_text:
                for post in user_posts:
                    if post["id"] == post_id:
                        post["comments"].append({
                            "username": session["username"],
                            "comment": comment_text
                        })
                        break
    
    # Handle search by poster username.
    search_query = request.args.get("search", "").strip().lower()
    if search_query:
        filtered_posts = [post for post in user_posts if search_query in post["username"].lower()]
    else:
        filtered_posts = user_posts

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Videos</title>
  <style>
    body { background-color: #2C3E50; color: white; font-family: Arial, sans-serif; }
    .header { background-color: #34495E; padding: 20px; text-align: center; border-radius: 10px; }
    .container { width: 90%; margin: 20px auto; }
    .post { border: 1px solid #ccc; background-color: #3C4F65; margin: 10px 0; padding: 10px; border-radius: 5px; }
    .media { max-width: 100%; height: auto; }
    .like, .comment-form { display: inline-block; margin-right: 10px; }
    .comment { margin-left: 20px; }
    input[type="text"] { padding: 5px; }
    input[type="submit"] {
        background-color: #3498DB; color: white; border: none; padding: 5px 10px;
        border-radius: 5px; cursor: pointer;
    }
    input[type="submit"]:hover { background-color: #2980B9; }
    form { margin: 5px 0; }
    .search { text-align: center; margin-bottom: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Videos / Posts</h1>
    <div class="search">
      <form method="GET" action="/videos">
         <input type="text" name="search" placeholder="Search by poster username">
         <input type="submit" value="Search">
      </form>
    </div>
  </div>
  <div class="container">
    {% for post in posts %}
      <div class="post">
        <p><strong>Posted by:</strong> {{ post.username }}</p>
        {% if post.caption %}
          <p><em>{{ post.caption }}</em></p>
        {% endif %}
        {% set ext = post.media.rsplit('.', 1)[-1].lower() %}
        {% if ext in ['png', 'jpg', 'jpeg', 'gif'] %}
          <img src="/uploads/{{ post.media }}" alt="Image" class="media">
        {% elif ext in ['mp4', 'mov', 'avi'] %}
          <video width="320" height="240" controls class="media">
            <source src="/uploads/{{ post.media }}" type="video/{{ ext }}">
            Your browser does not support the video tag.
          </video>
        {% else %}
          <a href="/uploads/{{ post.media }}">Download File</a>
        {% endif %}
        <p>Likes: {{ post.likes }}</p>
        <form method="POST" class="like">
          <input type="hidden" name="post_id" value="{{ post.id }}">
          <input type="submit" name="like" value="Like">
        </form>
        <div class="comments">
          {% for comment in post.comments %}
            <div class="comment">
              <p><strong>{{ comment.username }}:</strong> {{ comment.comment }}</p>
            </div>
          {% endfor %}
        </div>
        <form method="POST" class="comment-form">
          <input type="hidden" name="post_id" value="{{ post.id }}">
          <input type="text" name="comment" placeholder="Add a comment" required>
          <input type="submit" name="comment" value="Comment">
        </form>
      </div>
    {% else %}
      <p>No posts found.</p>
    {% endfor %}
    <br>
    <a href="/user">Back to Profile</a>
  </div>
</body>
</html>
""", posts=filtered_posts)


if __name__ == "__main__":
    app.run(debug=True)