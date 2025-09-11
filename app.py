from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587


TWILIO_SID = "ACc438143eda56682776a18bbd269416ce"
TWILIO_AUTH_TOKEN = "92e66484d12ef7b1d9d620e02213d89f"
TWILIO_PHONE = "+1 205 301 5366"
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


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
            error = "Seems like you dont have an account here. Try creating a new account"
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


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("login.html", user=session["user"])  


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# area to forget password
@app.route("/forget", methods=["GET", "POST"])
def forget():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")

        otp = str(random.randint(1000, 9999))
        session["otp"] = otp

        if email:
            if not email.endswith("@student.mmu.edu.my"):
                error = "Please use your student email"
                return render_template("forget.html", error=error)

            session["reset_email"] = email
            # to send OTP via outlook email
            try:
                msg = MIMEText(f"Your OTP code is: {otp}")
                msg["Subject"] = "Password Reset Code"
                msg["From"] = EMAIL_ADDRESS
                msg["To"] = email

                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, [email], msg.as_string())
                server.quit()
            except Exception as e:
                error = f"Email send failed: {str(e)}"
                return render_template("forget.html", error=error)

            return redirect(url_for("verify_otp"))

        elif phone:
            if not phone.isdigit():
                error = "Please enter a valid phone number"
                return render_template("forget.html", error=error)

            session["reset_phone"] = phone
            # to send the otp 
            try:
                client.messages.create(
                    body=f"Your OTP code is: {otp}",
                    from_=TWILIO_PHONE,
                    to=phone
                )
            except Exception as e:
                error = f"SMS send failed: {str(e)}"
                return render_template("forget.html", error=error)

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
            error = "Incorrect OTP"
    return render_template("verify_otp.html", error=error)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    error = None
    email = session.get("reset_email")
    phone = session.get("reset_phone")

    if not email and not phone:
        return redirect(url_for("forget"))

    if request.method == "POST":
        new_password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            error = "Passwords do not match"
            return render_template("reset_password.html", error=error, email=email, phone=phone)

        conn = get_db()
        cur = conn.cursor()
        if email:
            cur.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        elif phone:
            cur.execute("UPDATE users SET password=? WHERE phone=?", (new_password, phone))
        conn.commit()
        conn.close()

        flash("Password successfully reset. Please login.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", error=error, email=email, phone=phone)


if __name__ == "__main__":
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                phone TEXT,
                password TEXT)""")
    conn.commit()
    conn.close()
    app.run(debug=True)
