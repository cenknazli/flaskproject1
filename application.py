import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

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

    if authenticateUser(email, password) == "Registered":
        return render_template("authentication.html", result="Successfully Registered")
    elif authenticateUser(email, password) == "DB Error":
        return render_template("index.html", result="Error! Something went wrong while inserting data to database")
    elif authenticateUser(email, password) == "LoggedIn":
        return render_template("authentication.html", result="User logged in succesfully")
    elif authenticateUser(email, password) == "WrongPassword":
        return render_template("index.html", result="Error! Password is wrong")
    else:
        return render_template("failure.html", result="Error! What the hell is going on!")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    session.pop('user', None)
    return redirect('/')

def authenticateUser(email, password):
    # Check if email exists in db
    userID = db.execute("SELECT user_id FROM users WHERE email = :email",
            {"email": email}).fetchone()

    if userID is None:
        db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",
                    {"email": email, "password": password})
        try:
            db.commit()
            return "Registered"
        except:
            return "DB_Error"
    else:
        userID = db.execute("SELECT user_id FROM users WHERE email = :email and password = :password",
                {"email": email, "password": password}).fetchone()
        if userID:
            session['userID'] = userID[0]
            return "LoggedIn"
        else:
            return "WrongPassword"

@app.route("/search", methods=["POST"])
def search():
    #Get user entry from the searchBox
    searchText = request.form.get("searchBox")

    #Do not allow empty searchBox and show table if only there is a result matching
    if searchText:
        searchText = "'%" + searchText + "%'"
        query = "SELECT isbn, author, title, year FROM books WHERE isbn ilike " + searchText + " or author ilike " + searchText + " or title ilike " + searchText
        searchResults = db.execute(query).fetchall()
        if searchResults:
            return render_template("/search.html", showTable=True, results=searchResults)
        else:
            return render_template("/search.html", showTable=False, results="No Match! Try Again...")
    else:
        return render_template("/authentication.html", results="Please enter some information about book!")

@app.route("/search/<string:isbn>")
def bookDetail(isbn):
    #Get details from db
    bookDetails = db.execute("SELECT isbn, author, title, year FROM books WHERE isbn = :isbn",
                {"isbn": isbn}).fetchone()

    if bookDetails is None:
        return render_template("error.html", message = "No matching book!")

    session['isbn'] = isbn
    session['bookDetails'] = bookDetails

    #Check if book has review/reviewa
    existingComments = db.execute("SELECT cm.comment, usr.email FROM comments cm INNER JOIN users usr ON usr.user_id = cm.user_id WHERE isbn = :isbn",
                    {"isbn": isbn}).fetchall()

    #Get goodreads rating via api
    apiKey = 'jv4HdDgxRTDfmGn7VsPoWA'
    res = requests.get("https://www.goodreads.com/book/review_counts.json?key={" + apiKey + "}&isbns=" + isbn)

    if res.status_code != 200:
        raise Exception("Error: API request is unsuccessful!")

    data = res.json()
    bookRatingGoodreads = data["books"][0]["average_rating"]
    countOfReviews = data["books"][0]["reviews_count"]

    #If it has, show the review instead of commentbox
    if existingComments:
        return render_template("/book.html", bookDetails = bookDetails, existingComments = existingComments, bookRatingGoodreads = bookRatingGoodreads, countOfReviews = countOfReviews)

    return render_template("/book.html", bookDetails = bookDetails, bookRatingGoodreads = bookRatingGoodreads, countOfReviews = countOfReviews)

@app.route("/search/<string:isbn>", methods=["POST"])
def comment(isbn):
    #Get user entry and rating
    commentText = request.form.get("commentText")
    bookRating = request.form.get("rates")

    if commentText:
        db.execute("INSERT INTO comments (isbn, user_id, comment, rating) VALUES (:isbn, :user_id, :commentText, :rating)",
                {"isbn": session['isbn'], "user_id": session['userID'], "commentText": commentText, "rating": bookRating})
        try:
            db.commit()
            return render_template("/book.html", bookDetails = session['bookDetails'])
        except Exception as e:
            raise "db error, try again"
    else:
        raise "Ooops, you forgot to write something!"
