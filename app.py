from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import re
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

# -----------------------
# Database Configuration
# -----------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///participants.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)



# -----------------------
# Teams
# -----------------------
TEAMS = {
    "Red": "#e74c3c",
    "Blue": "#3498db",
    "Green": "#2ecc71",
    "Yellow": "#f1c40f"
}

# -----------------------
# Admin Credentials
# -----------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # CHANGE THIS

# -----------------------
# Model
# -----------------------
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    church = db.Column(db.String(100))
    team = db.Column(db.String(20))
    checked_in = db.Column(db.Boolean, default=False)
    question = db.Column(db.Text, nullable=True)
    anonymous = db.Column(db.Boolean, default=False)

# -----------------------
# Team Assignment Logic
# -----------------------
def assign_team(church):
    team_counts = {}

    for team in TEAMS.keys():
        church_count = Participant.query.filter_by(team=team, church=church).count()
        total_count = Participant.query.filter_by(team=team).count()
        team_counts[team] = (church_count, total_count)

    sorted_teams = sorted(team_counts.items(), key=lambda x: (x[1][0], x[1][1]))
    return sorted_teams[0][0]

# -----------------------
# Splash Page
# -----------------------
@app.route("/")
def splash():
    return render_template("splash.html")

# -----------------------
# Registration Page
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        church = request.form["church"]

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            flash("Please enter a valid email address.")
            return redirect(url_for("index"))

        if not phone.isdigit():
            flash("Phone number must contain digits only.")
            return redirect(url_for("index"))

        if len(phone) != 11:
            flash("Phone number must be exactly 11 digits.")
            return redirect(url_for("index"))

        existing = Participant.query.filter_by(email=email).first()
        if existing:
            flash("You are already registered. Please log in.")
            return redirect(url_for("login"))

        assigned_team = assign_team(church)

        question = request.form.get("question")
        anonymous = True if request.form.get("anonymous") else False

        new_user = Participant(
            name=name,
            email=email,
            phone=phone,
            church=church,
            team=assigned_team,
            question=question,
            anonymous=anonymous
        )

        db.session.add(new_user)
        db.session.commit()

        return render_template("success.html", name=name)

    churches = [
        "Biserica Maranata",
        "Biserica Connected Life",
        "Biserica Emaus",
        "Biserica Lui Hristos Leyton",
        "Other"
    ]

    return render_template("index.html", churches=churches)

# -----------------------
# User Login
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        user = Participant.query.filter_by(email=email).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("account"))
        else:
            flash("Email not found.")

    return render_template("login.html")

# -----------------------
# User Account
# -----------------------
@app.route("/account", methods=["GET", "POST"])
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = Participant.query.get(session["user_id"])

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("Your registration has been cancelled.")
        return redirect(url_for("index"))

    return render_template("account.html", user=user)
@app.route("/submit-question", methods=["POST"])
def submit_question():

    if "participant_id" not in session:
        return redirect(url_for("login"))

    participant = Participant.query.get(session["participant_id"])

    participant.question = request.form["question"]

    db.session.commit()

    flash("Your question has been submitted!")

    return redirect(url_for("account"))
# -----------------------
# User Logout
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -----------------------
# Admin Login
# -----------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.")

    return render_template("admin_login.html")

# -----------------------
# Admin Dashboard
# -----------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    participants = Participant.query.all()
    total_count = Participant.query.count()

    return render_template(
        "admin_dashboard.html",
        participants=participants,
        total_count=total_count,
        teams=TEAMS
    )

# -----------------------
# Admin Remove
# -----------------------
@app.route("/admin-remove/<int:participant_id>", methods=["POST"])
def admin_remove(participant_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    participant = db.session.get(Participant, participant_id)
    if participant:
        db.session.delete(participant)
        db.session.commit()
        flash("Participant removed successfully.")

    return redirect(url_for("admin_dashboard"))

# -----------------------
# Admin Check In
# -----------------------
@app.route("/admin-checkin/<int:participant_id>", methods=["POST"])
def admin_checkin(participant_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    participant = Participant.query.get_or_404(participant_id)
    participant.checked_in = True
    db.session.commit()

    flash("Participant checked in successfully.")
    return redirect(url_for("admin_dashboard"))

# -----------------------
# Admin Logout
# -----------------------
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

with app.app_context():
    db.create_all()
# -----------------------
# Run (Local Only)
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))