from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret_key"

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///participants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Participant model
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    church = db.Column(db.String(100))
    cancelled = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128), nullable=True)  # optional password


# Create database safely inside app context
with app.app_context():
    if not os.path.exists('participants.db'):
        db.create_all()


# Splash + Registration
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        church = request.form['church']

        # Check if participant already exists
        participant = Participant.query.filter_by(email=email).first()
        if participant:
            flash("You already registered! Please log in to manage your registration.")
            return redirect(url_for('login'))

        # Add new participant
        new_participant = Participant(name=name, email=email, phone=phone, church=church)
        db.session.add(new_participant)
        db.session.commit()
        return render_template("success.html", name=name)

    # Sample churches for combo box
    churches = ["Church A", "Church B", "Church C", "Church D"]
    return render_template("index.html", churches=churches)


# Participant login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        participant = Participant.query.filter_by(email=email).first()
        if participant:
            session['participant_id'] = participant.id
            return redirect(url_for('cancel'))
        else:
            flash("Email not found. Please register first.")
    return render_template("login.html")


# Cancel participation
@app.route("/cancel", methods=["GET", "POST"])
def cancel():
    if 'participant_id' not in session:
        return redirect(url_for('login'))

    participant = Participant.query.get(session['participant_id'])
    if request.method == "POST":
        participant.cancelled = True
        db.session.commit()
        flash("Your registration has been cancelled.")
        session.pop('participant_id', None)
        return redirect(url_for('index'))
    return render_template("cancel.html", participant=participant)


if __name__ == "__main__":
    # Use host='0.0.0.0' for testing on mobile devices in local network
    app.run(debug=True, host="0.0.0.0", port=5000)