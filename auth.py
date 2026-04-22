from flask import Blueprint, redirect, render_template, request, session
from flask_bcrypt import Bcrypt

from db import create_user, get_user, user_exists

auth = Blueprint("auth", __name__)
bcrypt = Bcrypt()


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user(username)
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/app")
        return render_template("login.html", error="Ugyldig brukernavn eller passord")
    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("register.html", error="Brukernavn og passord er påkrevd")
        if user_exists(username):
            return render_template("register.html", error="Brukernavnet er allerede i bruk")
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        create_user(username, hashed)
        return redirect("/login")
    return render_template("register.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")