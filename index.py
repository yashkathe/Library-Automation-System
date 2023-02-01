from flask import Flask, render_template, request, redirect
import RPi.GPIO as GPIO
from pymongo import MongoClient
import urllib.request
import json
import textwrap
import os

# DataBase config
cluster = MongoClient(os.environ.get("MONGO_URI"))


# GPIO config
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

app = Flask(__name__)
app.debug = True

# Home page route


@app.route("/")
def home():
    return render_template('home.html', headerText="Library automation Platform")

# Student pages route


@app.route("/student/home")
def irSensor():
    try:
        GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor
        while True:
            i = GPIO.input(11)
            if i == 0:  # When output from motion sensor is HIGH
                return render_template('student/student-home.html', message=[
                    "Student detected",
                    "Place your barcode in front of the camera"
                ],
                    mode="DETECTED",
                    headerText="Student Home"
                )
            elif i == 1:
                return render_template('student/student-home.html', message=[
                    "No Student detected"],
                    mode="NOTDETECTED",
                    headerText="Student Home"
                )
            else:
                return render_template('student/student-home.html', message=[
                    "PIR sensor is not connected to the system"],
                    headerText="Student Home",
                    mode="ERROR")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/student/QRlogin")
def qrLogin():
    try:
        post = {"email": "yash123", "pid": "123", "password": "123"}
        db = cluster["LibraryDB"]
        collection = db["books"]
        collection.insert_one(post)
        return render_template('student/qrlogin.html')
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/student/store-book")
def booksApi():
    try:
        base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
        with urllib.request.urlopen(base_api_link + "9781451648539") as f:
            text = f.read()
        decoded_text = text.decode("utf-8")
        # deserializes decoded_text to a Python object
        obj = json.loads(decoded_text)
        volume_info = obj["items"][0]
        authors = obj["items"][0]["volumeInfo"]["authors"]
        publisher = obj["items"][0]["volumeInfo"]["publisher"]
        image = obj["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]

        title = volume_info["volumeInfo"]["title"]
        description = textwrap.fill(
            volume_info["searchInfo"]["textSnippet"], width=65)
        pageCount = volume_info["volumeInfo"]["pageCount"]
        language = volume_info["volumeInfo"]["language"]

        return render_template('student/store-book.html', title=title, description=description, authors=authors, pageCount=pageCount, language=language, publisher=publisher, image=image)
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))

# Admin pages route


@app.route("/admin/home")
def irSensorAdmin():
    try:
        GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor
        while True:
            i = GPIO.input(11)
            if i == 0:  # When output from motion sensor is HIGH
                return render_template('admin/admin-home.html', message=[
                    "IR activated",
                    "The ISBN will be scanned now"
                ],
                    mode="DETECTED",
                    headerText="Admin Home Page")
            elif i == 1:
                return render_template('admin/admin-home.html', message=[
                    "IR Sensor not activated"],
                    mode="NOTDETECTED",
                    headerText="Admin Home Page")
            else:
                return render_template('admin/admin-home.html', message=[
                    "IR sensor is not connected to the system"],
                    mode="ERROR",
                    headerText="Admin Home Page")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/admin/store-book")
def storeBookAdmin():
    try:
        base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
        with urllib.request.urlopen(base_api_link + "9780307950284") as f:
            text = f.read()
        decoded_text = text.decode("utf-8")
        # deserializes decoded_text to a Python object
        obj = json.loads(decoded_text)
        volume_info = obj["items"][0]
        authors = obj["items"][0]["volumeInfo"]["authors"]
        publisher = obj["items"][0]["volumeInfo"]["publisher"]
        image = obj["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]

        title = volume_info["volumeInfo"]["title"]
        description = textwrap.fill(
            volume_info["searchInfo"]["textSnippet"], width=65)
        pageCount = volume_info["volumeInfo"]["pageCount"]
        language = volume_info["volumeInfo"]["language"]

        return render_template('admin/store-book.html', headerText="Store Book Data into Database", title=title, description=description, authors=authors, pageCount=pageCount, language=language, publisher=publisher, image=image)
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route('/admin/store-book-db', methods=['POST'])
def storeBookAdminPost():
    try:
        # Database settings
        db = cluster["LibraryDB"]
        collection = db["books"]

        # Collect data
        title = request.form["title"]
        description = request.form["description"]
        image = request.form["imageLink"]
        authors = request.form["authors"]
        pageCount = request.form["pageCount"]
        language = request.form["language"]
        publishers = request.form["publishers"]
        quantity = request.form["quantity"]

        # Check if the book already exists
        existingBook = collection.find_one(
            {"title": title, "language": language, "publishers": publishers})
        if existingBook:
            return render_template("error.html", headerText="Error", messageText="A book with similar title already exists")

        # Insert data
        collection.insert_one({
            "title": title,
            "description": description,
            "image": image,
            "authors": authors,
            "pageCount": pageCount,
            "language": language,
            "publishers": publishers,
            "quantity": quantity,
            "issuedBy": []
        })

        return render_template('admin/halt-page.html', headerText="Redirecting", messageText="Successfully Stored Data into the Database")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


# Error handling

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", headerText="Error 404", messageText="Couldn't find such route")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
