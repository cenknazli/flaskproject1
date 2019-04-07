import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

#Setup Database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def importData(isbn, title, author, year):
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year": year})
    try:
        db.commit()
        return "Imported"
    except:
        return "DBError"

with open('books.csv') as csvfile:
    fileReader = csv.reader(csvfile, delimiter=',')
    lineCount = 0
    for row in fileReader:
        if lineCount == 0:
            lineCount += 1
        else:
            if importData(row[0], row[1], row[2], row[3]) == "Imported":
                lineCount += 1
            else:
                print("Importing data can not completed!")
