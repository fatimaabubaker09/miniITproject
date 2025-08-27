from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


users = {"testuser": "password123"}

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            return redirect(url_for("profile"))
        else:
            return "Invalid username or password"
    return render_template("profile.html")

@app.route("/profile")
def profile():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
