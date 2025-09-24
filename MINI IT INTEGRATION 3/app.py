from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey_integration"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fitfriend.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

     #merged table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,        
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        phone TEXT,
        preferred_activity TEXT,
        frequency TEXT,
        level TEXT,
        goals TEXT,
        faculty TEXT,
        gender TEXT,
        age INTEGER,
        nickname TEXT,
        workouts TEXT,
        fitness_level TEXT,
        security_color TEXT,
        security_pets INTEGER,
        security_family TEXT
    )
    """)

    # activities table
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

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


@app.route("/")
def index():
    return redirect(url_for("login"))

#REGISTER PAGE 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email") or request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        phone = request.form.get("phone")

       
        security_color = request.form.get("security_color")
        security_pets = request.form.get("security_pets")
        security_family = request.form.get("security_family")

    
        if not email or not password:
            error = "Email and password are required."
            return render_template("register.html", error=error)

        if confirm_password and (password != confirm_password):
            error = "Passwords do not match."
            return render_template("register.html", error=error)

       
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (email, password, phone,
                                   security_color, security_pets, security_family)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email,
                password,
                phone,
                security_color,
                (int(security_pets) if security_pets and security_pets.isdigit() else None),
                security_family
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            error = "This email is already registered."
            return render_template("register.html", error=error)
        except Exception as e:
            conn.close()
            error = f"Database error: {e}"
            return render_template("register.html", error=error)

        conn.close()
        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email") or request.form.get("username")
        password = request.form.get("password")

        if not email or not password:
            error = "Please enter both email and password."
            return render_template("login.html", error=error)

        user = get_user_by_email(email)
        if user and user["password"] == password:
            session["user_email"] = user["email"]
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))
        else:
            error = "Incorrect username or password."

    return render_template("login.html", error=error)

#LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# PROFILE
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_email" not in session:
        return redirect(url_for("login"))

    saved = False
    if request.method == "POST" and request.form.get("delete_account") == "true":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = ?", (session["user_email"],))
        cur.execute("DELETE FROM activities WHERE user_id = ?", (session.get("user_id"),))
        conn.commit()
        conn.close()
        session.clear()
        flash("Account successfully deleted.")
        return redirect(url_for("login"))

    
    if request.method == "POST" and request.form.get("save_profile"):
        nickname = request.form.get("nickname")
        faculty = request.form.get("faculty")
        level = request.form.get("level")
        gender = request.form.get("gender")
        workouts = request.form.getlist("workouts")
        frequency = request.form.get("frequency")
        fitness_level = request.form.get("fitness_level")
        age = request.form.get("age")

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET nickname=?, faculty=?, level=?, gender=?, workouts=?, frequency=?, fitness_level=?, age=?
                WHERE email=?
            """, (
                nickname,
                faculty,
                level,
                gender,
                ",".join(workouts) if workouts else None,
                frequency,
                fitness_level,
                (int(age) if age and age.isdigit() else None),
                session["user_email"]
            ))
            conn.commit()
        except Exception as e:
            print("Error updating profile:", e)
        finally:
            conn.close()
        saved = True
        flash("Profile information saved successfully!")

    conn = get_db_connection()
    user_db = conn.execute("SELECT * FROM users WHERE email = ?", (session["user_email"],)).fetchone()
    conn.close()

    if not user_db:
        session.clear()
        return redirect(url_for("login"))

    user = {k: user_db[k] for k in user_db.keys()}

    return render_template("profile.html", user=user, saved=saved)

# EDIT PROFILE
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        nickname = request.form.get("nickname")
        age = request.form.get("age")
        faculty = request.form.get("faculty")
        level = request.form.get("level")
        gender = request.form.get("gender")
        preferred_activity = request.form.get("preferred_activity")
        goals = request.form.get("goals")
        workouts = request.form.get("workouts")  
        frequency = request.form.get("frequency")
        fitness_level = request.form.get("fitness_level")

        try:
            cur.execute("""
                UPDATE users
                SET name=?, nickname=?, age=?, faculty=?, level=?, gender=?,
                    preferred_activity=?, goals=?, workouts=?, frequency=?, fitness_level=?
                WHERE id=?
            """, (
                name,
                nickname,
                (int(age) if age and age.isdigit() else None),
                faculty,
                level,
                gender,
                preferred_activity,
                goals,
                workouts,
                frequency,
                fitness_level,
                session["user_id"]
            ))
            conn.commit()

            flash("Profile updated successfully!", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error updating profile: {e}", "error")

        finally:
            conn.close()

        return redirect(url_for("profile"))


    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("edit_profile.html", user=user)

# ACTIVITY PAGE
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

    activity_type = request.form.get("activity_type")
    duration = request.form.get("duration")
    distance = request.form.get("distance")
    date = request.form.get("date")

    if distance == "" or distance is None:
        distance_val = None
    else:
        try:
            distance_val = float(distance)
        except:
            distance_val = None

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO activities (user_id, activity, duration, distance, date)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], activity_type, duration, distance_val, date))
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

# FIND PARTNER
@app.route("/find_partner")
def find_partner():
    if "user_id" not in session:
        return redirect(url_for("login"))

    
    activity_pref = request.args.get("activity_preference")
    frequency = request.args.get("frequency")
    level = request.args.get("fitness_level")
    email_search = request.args.get("email_search")
    age_filter = request.args.get("age")
    faculty = request.args.get("faculty")

    
    query = """
        SELECT DISTINCT * FROM users
        WHERE id != ?
        AND email IS NOT NULL AND email != ''
    """
    params = [session["user_id"]]

   
    if activity_pref:
        query += " AND LOWER(workouts) = LOWER(?)"
        params.append(activity_pref)

    if frequency:
        query += " AND LOWER(frequency) = LOWER(?)"
        params.append(frequency)

    if level:
        query += " AND LOWER(fitness_level) = LOWER(?)"
        params.append(level)

    if email_search:
        query += " AND LOWER(email) LIKE LOWER(?)"
        params.append(f"%{email_search}%")

    if age_filter and age_filter.isdigit():
        query += " AND age = ?"
        params.append(int(age_filter))

    if faculty:
        query += " AND faculty = ?"
        params.append(faculty)

    
    conn = get_db_connection()
    partners = conn.execute(query, params).fetchall()
    conn.close()

    
    filters_applied = any([activity_pref, frequency, level, email_search, age_filter, faculty])

    return render_template(
        "find_partner.html",
        partners=partners,
        filters_applied=filters_applied,
        count=len(partners)
    )


#FORGET PASSWORD
@app.route("/forget", methods=["GET", "POST"])
def forget():
    error = None
    if request.method == "POST":
        security_color = request.form.get("security_color")
        security_pets = request.form.get("security_pets")
        security_family = request.form.get("security_family")

        if not security_color or not security_pets or not security_family:
            error = "Please answer all security questions."
            return render_template("forget.html", error=error)

        try:
            security_pets_int = int(security_pets)
        except ValueError:
            error = "Please enter a valid number for pets."
            return render_template("forget.html", error=error)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE LOWER(security_color)=? AND security_pets=? AND LOWER(security_family)=?",
                    (security_color.lower(), security_pets_int, security_family.lower()))
        user = cur.fetchone()
        conn.close()

        if not user:
            error = "Security answers do not match any account."
            return render_template("forget.html", error=error)

        session["reset_email"] = user["email"]
        return redirect(url_for("reset_password"))

    return render_template("forget.html", error=error)

#RESET PASSWORD
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session:
        flash("Please verify your security questions first.")
        return redirect(url_for("forget"))

    error = None
    if request.method == "POST":
        new_password = request.form.get("new_password") or request.form.get("password")
        confirm_password = request.form.get("confirm_password") or request.form.get("confirm")

        if not new_password or not confirm_password:
            error = "Please fill both password fields."
            return render_template("reset_password.html", error=error)

        if new_password != confirm_password:
            error = "Passwords do not match."
            return render_template("reset_password.html", error=error)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, session["reset_email"]))
            conn.commit()
        except Exception as e:
            error = f"Database error: {e}"
        finally:
            conn.close()

        session.pop("reset_email", None)
        flash("Password successfully reset. Please login.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", error=error)

# DELETE ACCOUNT 
@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activities WHERE user_id = ?", (session["user_id"],))
    cur.execute("DELETE FROM users WHERE id = ?", (session["user_id"],))
    conn.commit()
    conn.close()

    session.clear()
    flash("Account deleted.")
    return redirect(url_for("register"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

