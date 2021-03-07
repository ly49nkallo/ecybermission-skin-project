import os
import sqlite3
#!/SQL.py
import SQL

from types import MethodDescriptorType
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from header import login_required

# Configure CS50 Library to use SQLite database
db = SQL.SQL("sqlite:///users.db")

# Boiler plate stuff
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def apology(msg, errorCode="none"):
    return redirect(url_for('.error', msg = msg, code = errorCode))


@app.route("/error/<msg>/<code>")
def error(msg, code):
    return render_template("error.html", msg=msg, code=code)

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Enter username")
        for row in db.execute("SELECT username FROM users"):
            if str(row["username"]) == str(request.form.get("username")):
                return apology("Username already exists")
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Enter password")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))

    return render_template("register.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changePassword():
    """Allow users to change their passwords"""
    if request.method == "GET":
        return render_template("changePassword.html")
    else:
        if not request.form.get("currentPassword") or not request.form.get("newPassword") or not request.form.get("confirmPassword"):
            return apology("Must fill out all fields")
        password = request.form.get("currentPassword")
        npassword = request.form.get("newPassword")
        cpassword = request.form.get("confirmPassword")
        if not check_password_hash(db.execute("SELECT password_hash FROM users WHERE id = ?", session["user_id"])[0]["password_hash"], password):
            return apology("Incorrect password")
        if not npassword == cpassword:
            return apology("Passwords don't match")
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", generate_password_hash(str(npassword)), session["user_id"])
        return redirect("/logout")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

