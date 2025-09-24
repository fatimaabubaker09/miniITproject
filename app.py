from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db():
    # create the database in the same directory as the app (jst for mu info)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the correct table structure"""
    conn = get_db()
    cur = conn.cursor()
    
    # create the table if it doesn't exist
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT,
                faculty TEXT,
                level TEXT,
                gender TEXT,
                phone TEXT,
                security_color TEXT,
                security_pets INTEGER,
                security_family TEXT)""")
    
    # check if the table to add missing columns
    try:
       
        cur.execute("SELECT security_color, security_pets, security_family FROM users LIMIT 1")
    except sqlite3.OperationalError:
    
        print("Adding missing columns to users table...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN security_color TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN security_pets INTEGER")
            cur.execute("ALTER TABLE users ADD COLUMN security_family TEXT")
            print("Missing columns added successfully.")
        except sqlite3.OperationalError as e:
            print(f"Error adding columns: {e}")
    
    conn.commit()
    conn.close()

def save_to_json(user_data):
    """Save user data to a JSON file as backup"""
    try:
        # load existing data or create empty list
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users_backup.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        # add new user dataa
        user_data['timestamp'] = datetime.now().isoformat()
        user_data['id'] = len(data) + 1  
        data.append(user_data)
        
        # save back to file
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"User data saved to JSON: {user_data['email']}")
        
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def delete_from_json(email):
    """Delete user data from the JSON backup file"""
    try:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users_backup.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # filter out to see if they match anything 
            new_data = [user for user in data if user.get('email') != email]
            
            # save the updated data back to the file
            with open(json_path, 'w') as f:
                json.dump(new_data, f, indent=2)
                
            print(f"User data deleted from JSON: {email}")
            return True
        return False
        
    except Exception as e:
        print(f"Error deleting from JSON: {e}")
        return False

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
    
        email = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        phone = request.form.get("phone")
        security_color = request.form.get("security_color")
        security_pets = request.form.get("security_pets")
        security_family = request.form.get("security_family")

        print(f"Registration attempt: {email}") 

        # validate required fields
        if not all([email, password, confirm_password, phone, 
                   security_color, security_pets, security_family]):
            error = "All fields are required."
            return render_template("register.html", error=error)

        # check if passwords match
        if password != confirm_password:
            error = "Passwords do not match."
            return render_template("register.html", error=error)

        conn = get_db()
        cur = conn.cursor()

        # checking email exists or not 
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user:
            error = "This email is already registered."
            conn.close()
            return render_template("register.html", error=error)

        try:
            cur.execute("INSERT INTO users (email, password, phone, security_color, security_pets, security_family) VALUES (?, ?, ?, ?, ?, ?)", 
                       (email, password, phone, security_color, security_pets, security_family))
            conn.commit()
            
            # save
            save_to_json({
                'email': email,
                'password': password,
                'phone': phone,
                'security_color': security_color,
                'security_pets': security_pets,
                'security_family': security_family
            })
            
            conn.close()
            
           
            flash("Registration successful! You can now login.")
            return redirect(url_for("login"))
        except sqlite3.Error as e:
            error = f"Database error: {str(e)}"
            conn.close()
            return render_template("register.html", error=error)
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")

        print(f"Login attempt: {email} / {password}") 

        if not email or not password:
            error = "Please enter both email and password."
            return render_template("login.html", error=error)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user:
            print(f"User found: {user['email']}") 
            print(f"Stored password: {user['password']}") 
            print(f"Entered password: {password}") 
            print(f"Passwords match: {user['password'] == password}")

        if user and user["password"] == password:
            session["user"] = email
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))
        else:
            error = "Incorrect username or password."
    
    return render_template("login.html", error=error)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    # check if user is logged in
    if "user" not in session:
        return redirect(url_for("login"))
    
    # handling the  account deletion
    if request.method == "POST" and "delete_account" in request.form:
        # delete account from database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email=?", (session["user"],))
        conn.commit()
        conn.close()
        
        # delete account from JSON backup
        delete_from_json(session["user"])
        
        # clear session and show confirmation
        session.clear()
        flash("Account successfully deleted!")
        return redirect(url_for("login"))
    
    # handle profile update (nickname, faculty, level, gender, workouts, frequency, fitness_level, age)
    saved = False
    if request.method == "POST" and "save_profile" in request.form:
        nickname = request.form.get("nickname")
        faculty = request.form.get("faculty")
        level = request.form.get("level")
        gender = request.form.get("gender")
        workouts = request.form.getlist("workouts")
        frequency = request.form.get("frequency")
        fitness_level = request.form.get("fitness_level")
        age = request.form.get("age")
        
        if nickname:
            session["nickname"] = nickname
        if faculty:
            session["faculty"] = faculty
        if level:
            session["level"] = level
        if gender:
            session["gender"] = gender
        if workouts:
            session["workouts"] = ",".join(workouts)
        if frequency:
            session["frequency"] = frequency
        if fitness_level:
            session["fitness_level"] = fitness_level
        if age:
            session["age"] = age
            
        # ipdate database with faculty, level, and gender
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET faculty=?, level=?, gender=? WHERE email=?", 
                       (faculty, level, gender, session["user"]))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating user profile: {e}")
        finally:
            conn.close()
            
        saved = True
        flash("Profile information saved successfully!")
    
    # get user data from database
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (session["user"],))
    user_db = cur.fetchone()
    conn.close()
    
    if not user_db:
        session.pop("user", None)
        return redirect(url_for("login"))
    
    user = {
        "email": user_db["email"],
        "faculty": user_db["faculty"] or session.get("faculty", ""),
        "level": user_db["level"] or session.get("level", ""),
        "gender": user_db["gender"] or session.get("gender", ""),
        "phone": user_db["phone"],
        "nickname": session.get("nickname", "")
    }
    
    return render_template("profile.html", user=user, saved=saved)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/forget", methods=["GET", "POST"])
def forget():
    error = None
    if request.method == "POST":
        security_color = request.form.get("security_color")
        security_pets = request.form.get("security_pets")
        security_family = request.form.get("security_family")

        print(f"Forget password attempt") 
        print(f"Answers: Color={security_color}, Pets={security_pets}, Family={security_family}")  # Debug

        # to check if theyrs answered or not
        if not security_color or not security_pets or not security_family:
            error = "Please answer all security questions."
            return render_template("forget.html", error=error)
        
        conn = get_db()
        cur = conn.cursor()
        
        
        try:
            security_pets_int = int(security_pets)
        except ValueError:
            error = "Please enter a valid number for pets."
            conn.close()
            return render_template("forget.html", error=error)
        
    
        cur.execute("SELECT * FROM users WHERE LOWER(security_color)=? AND security_pets=? AND LOWER(security_family)=?", 
                   (security_color.lower(), security_pets_int, security_family.lower()))
        user = cur.fetchone()
        conn.close()
        
        if not user:
            error = "Security answers do not match any account. Please try again."
            return render_template("forget.html", error=error)
        
        print(f"Found user: {user['email']}")  
        print("Answers correct, redirecting to reset_password")  
        
        # stor ingemail in session for password reset
        session["reset_email"] = user["email"]
        return redirect(url_for("reset_password"))

    return render_template("forget.html", error=error)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    error = None
    email = session.get("reset_email")

    if not email:
        # if no email in session, redirect to forget password page
        flash("Please verify your security questions first.")
        return redirect(url_for("forget"))

    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            error = "Please fill in all password fields."
            return render_template("reset_password.html", error=error)

        if new_password != confirm_password:
            error = "Passwords do not match"
            return render_template("reset_password.html", error=error)

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
            conn.commit()
            conn.close()
            
            # clear the reset session data
            session.pop("reset_email", None)
            
            flash("Password successfully reset. Please login.")
            return redirect(url_for("login"))
        except sqlite3.Error as e:
            error = f"Database error: {str(e)}"
            conn.close()
            return render_template("reset_password.html", error=error)

    return render_template("reset_password.html", error=error)

if __name__ == "__main__":
    # initialize the database
    init_db()
    app.run(debug=True)









