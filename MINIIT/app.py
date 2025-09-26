from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"   



# Database 

def init_db():
    conn = sqlite3.connect("fitfriend.db")
    c = conn.cursor()

    # users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            preferred_activity TEXT,
            frequency TEXT,
            level TEXT,
            goals TEXT
        )
    """)

    # the table for activity
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity TEXT,
            duration INTEGER,
            distance REAL,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect("fitfriend.db")
    conn.row_factory = sqlite3.Row
    return conn


#route
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        preferred_activity = request.form.get("preferred_activity")
        frequency = request.form.get("frequency")
        level = request.form.get("level")
        goals = request.form.get("goals")

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (name, email, password, preferred_activity, frequency, level, goals)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, password, preferred_activity, frequency, level, goals))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))
        else:
            return "Invalid credentials"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()

    return render_template("profile.html", user=user)

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()

    # Delete activities
    c.execute("DELETE FROM activities WHERE user_id = ?", (session["user_id"],))

    # Delete account
    c.execute("DELETE FROM users WHERE id = ?", (session["user_id"],))

    conn.commit()
    conn.close()

    session.clear()
    return redirect(url_for("register"))  # redirect to registration page after deleting account


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        preferred_activity = request.form.get("preferred_activity")
        frequency = request.form.get("frequency")
        level = request.form.get("level")
        goals = request.form.get("goals")

        c.execute("""
            UPDATE users
            SET name = ?, email = ?, preferred_activity = ?, frequency = ?, level = ?, goals = ?
            WHERE id = ?
        """, (name, email, preferred_activity, frequency, level, goals, session["user_id"]))
        
        conn.commit()
        conn.close()
        return redirect(url_for("profile"))

    
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("edit_profile.html", user=user)


@app.route("/activity")
def activity():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    activities = conn.execute("SELECT * FROM activities WHERE user_id = ? ORDER BY date DESC", 
                              (session["user_id"],)).fetchall()
    conn.close()

    return render_template("activity.html", activities=activities)


@app.route("/add_activity", methods=["POST"])
def add_activity():
    if "user_id" not in session:
        return redirect(url_for("login"))

    activity_type = request.form["activity_type"]
    duration = request.form["duration"]
    distance = request.form.get("distance")
    date = request.form["date"]


    if distance == "" or distance is None:
        distance = None
    else:
        distance = float(distance)  

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO activities (user_id, activity, duration, distance, date)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], activity_type, duration, distance, date))
    conn.commit()
    conn.close()

    return redirect(url_for("activity"))


@app.route("/delete_activity/<int:activity_id>", methods=["POST"])
def delete_activity(activity_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM activities WHERE id = ? AND user_id = ?", (activity_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect(url_for("activity"))


@app.route("/find_partner")
def find_partner():
    if "user_id" not in session:
        return redirect(url_for("login"))

    activity_pref = request.args.get("activity_preference")
    frequency = request.args.get("frequency")
    level = request.args.get("fitness_level")
    email_search = request.args.get("email_search")

    query = "SELECT * FROM users WHERE id != ?"
    params = [session["user_id"]]

    if activity_pref:
        query += " AND preferred_activity = ?"
        params.append(activity_pref)
    if frequency:
        query += " AND frequency = ?"
        params.append(frequency)
    if level:
        query += " AND level = ?"
        params.append(level)
    if email_search:
        query += " AND email LIKE ?"
        params.append(f"%{email_search}%")

    conn = get_db_connection()
    partners = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("find_partner.html", partners=partners, filters_applied=bool(activity_pref or frequency or level or email_search), count=len(partners))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)














