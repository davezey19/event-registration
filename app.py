from flask import Flask, render_template, request, redirect
import csv
import os

app = Flask(__name__)

# Create CSV file if it doesn't exist
if not os.path.exists("registrations.csv"):
    with open("registrations.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Email", "Phone"])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]

    with open("registrations.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, email, phone])

    return redirect("/success")

@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    app.run()