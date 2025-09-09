from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

USER_FILE = "users.json"

if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

login_attempts = {}

def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            if username not in login_attempts:
                login_attempts[username] = 0

            stored = users[username]
            real_password = stored if isinstance(stored, str) else stored.get("password")

            if real_password == password:
                login_attempts[username] = 0
                session["username"] = username  
                return redirect(url_for("profile")) 
            else:
                login_attempts[username] += 1
                if login_attempts[username] >= 3:
                    return '''
                        Can't remember your password? 
                        <a href="/forget">Click Forget Password</a>
                    '''
                return render_template("profile.html", error=f"Incorrect password! Attempt {login_attempts[username]} of 3")
        else:
            return render_template("profile.html", error="Seems like you dont have an account here. Try creating a new account")

    return render_template("profile.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    username = session.get("username")

    if not username:
        return redirect(url_for("login"))

    if request.method == "POST":
        nickname = request.form.get("nickname")
        workouts = request.form.getlist("workouts")
        times = request.form.getlist("times")

        users[username] = {
            "password": users[username] if isinstance(users[username], str) else users[username]["password"],
            "nickname": nickname,
            "workouts": workouts,
            "times": times
        }
        save_users()
        
        return render_template("login.html", user=users[username], saved=True)

    user_profile = users.get(username, {}) 
    return render_template("login.html", user=user_profile, saved=False)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return render_template("register.html", error="User already exists!")

        users[username] = password
        save_users()
        login_attempts[username] = 0
    
        return render_template("profile.html", success="Account created successfully! Please log in.")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/forget")
def forget():
    return render_template("forget.html")

if __name__ == "__main__":
    app.run(debug=True)
