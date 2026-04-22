from flask import Blueprint, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
import json

auth = Blueprint("auth", __name__)
bcrypt = Bcrypt()

def load_users():
    try:
        with open("users.json") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()
        user = users.get(username)

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/app")

        return "Invalid login"

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()

        if username in users:
            return "User exists"

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        users[username] = {"password": hashed}

        save_users(users)

        return redirect("/login")

    return render_template("register.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")