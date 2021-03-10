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
from datetime import datetime
from flask_mail import Mail
from flask_mail import Message

from header import login_required, lookup, lookup_by_geocode

# Configure CS50 Library to use SQLite database
db = SQL.SQL("sqlite:///users.db")

# Boiler plate stuff
app = Flask(__name__)
mail = Mail(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["TEMPLATES_AUTO_RELOAD"] = True
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


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def apology(msg, errorCode="none"):
    return redirect(url_for('error', msg = str(msg), code = errorCode))


@app.route("/error/<msg>/<code>")
def error(msg, code):
    if code == "none" or not RepresentsInt(code):
        return render_template("error.html", msg=msg, code="")
    return render_template("error.html", msg=msg, code=code)


@app.route("/")
@login_required
def index():
    geocode = db.execute("SELECT zip FROM users WHERE id=?", session["user_id"])[0]["zip"]
    if geocode == None:
        return redirect("/register/survey")
    cache = lookup_by_geocode(geocode)
    for row in cache["hourly"]:
        row["disc"] = row["weather"][0]["description"]
        row["time"] = datetime.utcfromtimestamp(int(row["dt"])).strftime('%m/%d %H')
    
    # Test mailing system
    # msg = Message("hello", sender="tyabrennan@gmail.com", recipients=["tyabrennan@gmail.com"])
    # mail.send(msg)
    return render_template("index.html", zip=geocode, lat=cache["lat"], lon=cache["lon"], d=cache["current"], 
            weather=cache["current"]["weather"][0]["description"], forecast=cache["hourly"])




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
        return redirect("/login")

    return render_template("register.html")


@app.route("/register/survey", methods=["GET", "POST"])
@login_required
def survey():
    z = db.execute("SELECT email,zip FROM users WHERE id=?", session["user_id"])[0]
    if request.method == "POST":
        zip=request.form.get("zip")
        email = request.form.get("email")
        if not request.form.get("zip") and not z["zip"]:
            return apology("Please record a zipcode")
        if not RepresentsInt(zip) and zip != None:
            return apology("Zipcode is not an int")
        db.execute("UPDATE users SET zip=?, email=? WHERE id=?", zip, str(email), session["user_id"])
        return redirect("/")
    x = db.execute("SELECT email,zip FROM users WHERE id=?", session["user_id"])[0]
    email = x["email"]
    zip = x["zip"]
    return render_template("survey.html", email=email, zip=zip)


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

