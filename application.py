import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/authentication", methods=["POST"])
def authSuccess():
    # Get email and password from the form
    email = request.form.get("authFormEmail")
    password = request.form.get("authFormPassword")

    if authenticateUser(email, password) == 1:
        return render_template("authentication.html", result="Successfully Registered")
    elif authenticateUser(email, password) == -1:
        return render_template("authentication.html", result="Error! Something went wrong while inserting data to database")
    elif authenticateUser(email, password) == 2:
        return render_template("authentication.html", result="User logged in succesfully")
    elif authenticateUser(email, password) == -2:
        return render_template("authentication.html", result="Error! Password is wrong")
    else:
        return render_template("failure.html", result="Error! What the hell is going on!")

def authenticateUser(email, password):
    # Check if email is exist in db
    user = db.execute("SELECT user_id FROM users WHERE email = :email",
            {"email": email}).fetchone()

    if user is None:
        db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",
                    {"email": email, "password": password})
        try:
            db.commit()
            return 1
        except:
            return -1
    else:
        user =  db.execute("SELECT user_id FROM users WHERE password = :password AND email = :email",
                {"password": password, "email": email}).fetchone()
        if user is None:
            return -2
        else:
            return 2
