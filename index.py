from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import urllib.request
import argparse
import RPi.GPIO as GPIO
from imutils.video import VideoStream
from pyzbar import pyzbar
import cv2
from bson import ObjectId
import json
import textwrap
import os
import imutils
import time

# DataBase config
cluster = MongoClient(os.environ.get("MONGO_URI"))


# GPIO config
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

app = Flask(__name__)
app.secret_key = "XXt4FjJOkvMteX9YUu30f3cidxr3WbFv"
app.debug = True

# Home page route


@app.route("/")
def home():
    return render_template('home.html', headerText="Library automation Platform")

# Student pages route


@app.route("/student/auth/halt-page")
def loginHaltStudent():
    try:
        GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor
        while True:
            i = GPIO.input(11)
            if i == 0:  # When output from motion sensor is HIGH
                return render_template('shared/halt-page.html',
                                       messageText="Place your QR Code in front of camera to login now",
                                       headerText="Student LOGIN",
                                       redirectLink="/student/auth/login",
                                       mode="DETECTED"
                                       )
            elif i == 1:
                return render_template('shared/halt-page.html',
                                       messageText="interact with IR sensor when you are ready with your login barcode",
                                       headerText="Student Login")
            else:
                return render_template('shared/halt-page.html',
                                       messageText="Not IR sensor detected",
                                       headerText="ERROR")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/student/auth/login")
def qrLogin():
    try:
        # setup database
        db = cluster["LibraryDB"]
        collection = db["users"]
        # start pi camera for qr code scanning
        ap = argparse.ArgumentParser()
        ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                        help="path to output CSV file containing barcodes")
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        args = vars(ap.parse_args())
        # vs = VideoStream(usePiCamera=True).start()  # For Pi Camera
        time.sleep(0.1)
        while True:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h),
                              (0, 0, 255), 2)
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type
                if (barcodeData):
                    vs.stop()
                    print(barcodeData)
                    user = collection.find_one(
                        {"_id": ObjectId(barcodeData)})
                    if (user):
                        print(user)
                        session["student"] = barcodeData
                        return redirect(url_for("booksApi"))
                    else:
                        raise Exception(
                            "No account found, try again later")
    except Exception as e:
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        vs.stop()
        print(e)
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


@app.route("/admin/auth/halt-page")
def loginHaltAdmin():
    try:
        GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor
        while True:
            i = GPIO.input(11)
            if i == 0:  # When output from motion sensor is HIGH
                return render_template('shared/halt-page.html',
                                       messageText="Place your QR Code in front of camera to login now",
                                       headerText="Admin LOGIN",
                                       redirectLink="/admin/auth/login",
                                       mode="DETECTED"
                                       )
            elif i == 1:
                return render_template('shared/halt-page.html',
                                       messageText="interact with IR sensor when you are ready with your login barcode",
                                       headerText="Admin Login")
            else:
                return render_template('shared/halt-page.html',
                                       messageText="Not IR sensor detected",
                                       headerText="ERROR")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/admin/auth/login")
def loginAdmin():
    try:
        # setup database

        db = cluster["LibraryDB"]
        collection = db["users"]

        # start pi camera for qr code scanning

        ap = argparse.ArgumentParser()
        ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                        help="path to output CSV file containing barcodes")
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        args = vars(ap.parse_args())
        # vs = VideoStream(usePiCamera=True).start()  # For Pi Camera
        time.sleep(0.1)

        while True:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type
                if (barcodeData):
                    vs.stop()
                    print(barcodeData)
                    user = collection.find_one({"_id": ObjectId(barcodeData)})
                    if (user):
                        print(user)
                        session["admin"] = barcodeData
                        return redirect(url_for("irSensorAdmin"))
                    else:
                        raise Exception("No account found, try again later")
    except Exception as e:
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        vs.stop()
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/admin/home")
def irSensorAdmin():
    try:
        VideoStream(src=0).stop()
        sessionAdmin = session["admin"]
        if (sessionAdmin):
            return render_template('shared/shared-home.html', message=[
                "Started Scanning",
                "The ISBN will be scanned now"
            ],
                mode="DETECTED",
                headerText="Admin Home Page")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/admin/store-book")
def storeBookAdmin():
    try:
        sessionAdmin = session["admin"]
        if (sessionAdmin):
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
        else:
            raise Exception("No Sessions found. Please login first")
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

        return render_template('admin/halt-page.html', headerText="Redirecting", messageText="Successfully Stored Data into the Database", redirectLink="/admin/home")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


# Error handling for 404 requests

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", headerText="Error 404", messageText="Couldn't find such route")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
