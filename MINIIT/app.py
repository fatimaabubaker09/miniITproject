from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# -------------------------
# Mock data
# -------------------------

# Partner data (you could later fetch this from a database)
partners = [
    {
        "name": "Chu Wanning",
        "activities": ["Running", "Yoga"],
        "frequency": "Daily",
        "level": "Intermediate",
        "goals": "Improve endurance and flexibility",
        "email": "3799steps@student.mmu.edu.my"
    },
    {
        "name": "Mo Ran",
        "activities": ["Weight Training", "Cycling"],
        "frequency": "Several times a week",
        "level": "Advanced",
        "goals": "Build strength and muscle",
        "email": "moron@student.mmu.edu.my"
    },
    {
        "name": "Murong Chuyi",
        "activities": ["Swimming", "Hiking"],
        "frequency": "Weekly",
        "level": "Beginner",
        "goals": "Lose weight and tone muscles",
        "email": "no.longer.here@student.mmu.edu.my"
    },
    {
        "name": "Jason Todd",
        "activities": ["Running", "Weight Training"],
        "frequency": "Daily",
        "level": "Intermediate",
        "goals": "Train for marathon",
        "email": "crowbar_lover@student.mmu.edu.my"
    },
]

# In-memory activity log
activities = [
    {"id": 1, "date": "2023-10-15", "activity": "Running", "duration": "30 mins", "distance": "5.2 km"},
    {"id": 2, "date": "2023-10-14", "activity": "Weight Training", "duration": "45 mins", "distance": ""},
    {"id": 3, "date": "2023-10-12", "activity": "Cycling", "duration": "60 mins", "distance": "15.7 km"},
    {"id": 4, "date": "2023-10-10", "activity": "Yoga", "duration": "40 mins", "distance": ""}
]


# -------------------------
# Routes
# -------------------------

@app.route("/")
def home():
    return redirect(url_for("find_partner"))


@app.route("/find-partner", methods=["GET"])
def find_partner():
    activity_pref = request.args.get("activity_preference", "")
    frequency = request.args.get("frequency", "")
    fitness_level = request.args.get("fitness_level", "")

    # Filtering logic
    filtered = []
    for p in partners:
        if activity_pref and activity_pref not in p["activities"]:
            continue
        if frequency and frequency != p["frequency"]:
            continue
        if fitness_level and fitness_level != p["level"]:
            continue
        filtered.append(p)

    return render_template("find_partner.html", partners=filtered, count=len(filtered))


@app.route("/activity", methods=["GET"])
def activity():
    return render_template("activity.html", activities=activities)


@app.route("/add_activity", methods=["POST"])
def add_activity():
    global activities
    activity_type = request.form.get("activity_type")
    duration = request.form.get("duration")
    distance = request.form.get("distance", "")
    date = request.form.get("date")

    new_id = max([a["id"] for a in activities]) + 1 if activities else 1
    new_activity = {
        "id": new_id,
        "date": date,
        "activity": activity_type,
        "duration": f"{duration} mins",
        "distance": f"{distance} km" if distance else ""
    }
    activities.append(new_activity)

    return redirect(url_for("activity"))


@app.route("/delete_activity/<int:activity_id>", methods=["POST"])
def delete_activity(activity_id):
    global activities
    activities = [a for a in activities if a["id"] != activity_id]
    return redirect(url_for("activity"))


@app.route("/profile")
def profile():
    return "<h1>Profile Page (coming soon)</h1>"


@app.route("/logout")
def logout():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)

