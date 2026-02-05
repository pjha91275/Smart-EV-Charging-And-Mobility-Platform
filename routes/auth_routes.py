from flask import Blueprint, render_template, request, redirect, session
from models.db import get_db

auth_bp = Blueprint("auth", __name__)

# Registration
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        role = request.form["role"].strip()  # user / owner

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, password, role)
            )
            conn.commit()
        except:
            return "Email already exists"
        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html")


# Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, role, blacklisted FROM users WHERE lower(email)=? AND password=?",
            (email, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            # user[2] is blacklisted flag
            if len(user) > 2 and user[2]:
                return "Account is blacklisted"
            session["user_id"] = user[0]
            session["role"] = user[1]

            if user[1] == "user":
                return redirect("/user/dashboard")
            else:
                return redirect("/owner/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


# Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
