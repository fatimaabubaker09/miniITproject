from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import smtplib
from email.message import EmailMessage
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

EMAIL_ADDRESS = "fitfriend4@gmail.com"
EMAIL_PASSWORD = "emfy mekt kxmc knvg"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user:
            error = "This email is already registered."
            return render_template("register.html", error=error)

        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect(url_for("profile"))
        else:
            error = "Incorrect username or password."
    return render_template("login.html", error=error)


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html", user=session["user"])


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/forget", methods=["GET", "POST"])
def forget():
    error = None
    if request.method == "POST":
        email = request.form.get("email")

        if not email or not email.endswith("@gmail.com"):
            error = "Please enter a valid Gmail address."
            return render_template("forget.html", error=error)

    
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        session["otp"] = otp
        session["reset_email"] = email

        try:
            msg = EmailMessage()
            msg["Subject"] = "OTP Verification"
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = email
            msg.set_content("Your OTP is: " + otp)

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            error = f"Email send failed: {str(e)}"
            return render_template("forget.html", error=error)

        flash("OTP has been sent to your Gmail.")
        return redirect(url_for("verify_otp"))

    return render_template("forget.html", error=error)


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    error = None
    if request.method == "POST":
        entered_otp = request.form["otp"]
        if entered_otp == session.get("otp"):
            return redirect(url_for("reset_password"))
        else:
            error = "Invalid OTP. Please try again."
    return render_template("verify_otp.html", error=error)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    error = None
    email = session.get("reset_email")

    if not email:
        return redirect(url_for("forget"))

    if request.method == "POST":
        new_password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            error = "Passwords do not match"
            return render_template("reset_password.html", error=error, email=email)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        conn.commit()
        conn.close()

        flash("Password successfully reset. Please login.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", error=error, email=email)


if __name__ == "__main__":
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT)""")
    conn.commit()
    conn.close()
    app.run(debug=True)

