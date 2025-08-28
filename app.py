from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# to store registered users
users = {}

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        student_email = request.form["username"]  
        password = request.form["password"]

        if student_email in users:
            if users[student_email] == password:
                return redirect(url_for("profile"))
            else:
                error = "Incorrect password!"
        else:
            error = "You don’t have an account, try creating a new account."

    return render_template("profile.html", error=error)

@app.route("/profile")
def profile():
    return "<h1>Welcome to your profile page!</h1>"

# REGISTER PAGE
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_email = request.form["username"]
        password = request.form["password"]

        if student_email in users:
            return "User already exists!"
        users[student_email] = password
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)