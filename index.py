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
import serial
from mfrc522 import SimpleMFRC522
from time import sleep

# DataBase config
cluster = MongoClient(os.environ.get("MONGO_URI"))

# GPIO config
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

app = Flask(__name__)
app.secret_key = "XXt4FjJOkvMteX9YUu30f3cidxr3WbFv"
app.debug = True

db = cluster["LibraryDB"]

# Home page route


@app.route("/")
def home():
    session["student"] = None
    session["admin"] = None
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
        collection = db["users"]
        # start pi camera for qr code scanning
        ap = argparse.ArgumentParser()
        ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                        help="path to output CSV file containing barcodes")
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
                if (barcodeData):
                    vs.stop()
                    print(barcodeData)
                    user = collection.find_one(
                        {"_id": ObjectId(barcodeData)})
                    if (user):
                        print(user)
                        session["student"] = barcodeData
                        return redirect(url_for("returnOrIssue"))
                    else:
                        raise Exception(
                            "No account found, try again later")
    except Exception as e:
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        vs.stop()
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/student/select-option")
def returnOrIssue():
    try:
        sessionStudent = session["student"]
        if(sessionStudent):
            collection = db["users"]
            user = collection.find_one({"_id": ObjectId(session["student"])})
            return render_template('student/issueOrReturn.html', headerText="Welcome " + user["email"])
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/student/issue-home")
def issueBook():
    try:
        sessionStudent = session["student"]
        if(sessionStudent):
            return render_template('shared/shared-home.html', message=[
                "Started Scanning",
                "The ISBN will be scanned now"
            ],
                mode="DETECTED",
                headerText="Issuing Book",
                redirectLink="/student/issue-book-db")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))

@app.route("/student/issue-book-db")
def issueBookDB():
    try:
        sessionStudent = session["student"]
        if(sessionStudent):
            # scanning isbn code will go here
            barcode = "9781451648539"
            
            if(barcode):
                bookCollection = db["books"]
                userCollection = db["users"]
                existingBook = bookCollection.find_one(
                        {"isbn": barcode})
                if(existingBook):

                    #update book collection
                    myquery = { "isbn": existingBook["isbn"] }
                    updatedQuantity =  int(existingBook["quantity"]) - 1
                    newvalues = { "$set": { "quantity": updatedQuantity  } }
                    bookCollection.update_one(myquery, newvalues)
                    newvalues = { "$push": { "issuedBy": ObjectId(sessionStudent) } }
                    bookCollection.update_one(myquery, newvalues)

                    #update user collection
                    myquery = { "_id": ObjectId(session["student"]) }
                    newvalues = { "$push": { "booksIssued": existingBook["isbn"] } }
                    userCollection.update_one(myquery, newvalues)

                    return render_template('shared/halt-page.html', headerText="Redirecting", messageText="Successfully Stored Data into the Database", redirectLink="/student/select-option")
                else:
                    raise Exception("There is no such book in a databse")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))

@app.route("/student/return-home")
def returnBook():
    try:
        sessionStudent = session["student"]
        if(sessionStudent):
            return render_template('shared/shared-home.html', message=[
                "Started Scanning",
                "The ISBN will be scanned now"
            ],
                mode="DETECTED",
                headerText="Returning Book",
                redirectLink="/student/return-book-db")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e))

@app.route("/student/return-book-db")
def returnBookDB():
    try:
        sessionStudent = session["student"]
        if(sessionStudent):
            # scanning isbn code will go here
            barcode = "9781451648539"
            
            if(barcode):
                bookCollection = db["books"]
                userCollection = db["users"]
                existingBook = bookCollection.find_one(
                        {"isbn": barcode})
                if(existingBook):

                    #update book collection
                    myquery = { "isbn": existingBook["isbn"] }
                    updatedQuantity =  int(existingBook["quantity"]) + 1
                    newvalues = { "$set": { "quantity": updatedQuantity  } }
                    bookCollection.update_one(myquery, newvalues)
                    newvalues = { "$pull": { "issuedBy": ObjectId(sessionStudent) } }
                    bookCollection.update_one(myquery, newvalues)

                    #update user collection
                    myquery = { "_id": ObjectId(session["student"]) }
                    newvalues = { "$pull": { "booksIssued": existingBook["isbn"] } }
                    userCollection.update_one(myquery, newvalues)

                    return render_template('shared/halt-page.html', headerText="Redirecting", messageText="Successfully Stored Data into the Database", redirectLink="/student/select-option")
                else:
                    raise Exception("There is no such book in a databse")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
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
                    print(user)
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
                headerText="Admin Home Page",
                redirectLink="/admin/store-book")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route("/admin/store-book")
def storeBookAdmin():
    try:
        sessionAdmin = session["admin"]
        if (sessionAdmin):
            while True:
                # # configure the serial port
                # ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

                # # wait for the scanner to initialize
                # time.sleep(1)

                # barcode = ""
                # # read the data from the serial port
                # data = ser.read(13)
                # # decode the barcode data
                # barcode = data.decode('utf-8')
                barcode = "9781451648539"
                if (barcode):
                    print(barcode)
                    # check if book with similar isbn exists
                    collection = db["books"]
                    existingBook = collection.find_one(
                        {"isbn": barcode})
                    if (existingBook):
                        print(existingBook)
                        print(existingBook['title'])
                        return render_template('admin/store-book.html',
                                               headerText="Store Book Data into Database",
                                               title=existingBook['title'],
                                               description=existingBook['description'],
                                               authors=existingBook['authors'],
                                               pageCount=existingBook['pageCount'],
                                               language=existingBook['language'],
                                               quantity=existingBook['quantity'],
                                               image=existingBook['image'],
                                               isbn=barcode,
                                               showBox="yes"
                                               )

                    base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
                    with urllib.request.urlopen(base_api_link + barcode) as f:
                        text = f.read()
                    decoded_text = text.decode("utf-8")
                    # deserializes decoded_text to a Python object
                    obj = json.loads(decoded_text)

                    # check if books exists
                    if obj["totalItems"] == 0:
                        return render_template("error.html", headerText="Error", messageText="Google Books API has no data for the given ISBN")

                    volume_info = obj["items"][0]
                    authors = obj["items"][0]["volumeInfo"]["authors"]
                    image = obj["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
                    title = volume_info["volumeInfo"]["title"]
                    description = textwrap.fill(
                        volume_info["searchInfo"]["textSnippet"], width=65)
                    pageCount = volume_info["volumeInfo"]["pageCount"]
                    language = volume_info["volumeInfo"]["language"]
                    return render_template('admin/store-book.html',
                                           headerText="Store Book Data into Database",
                                           title=title,
                                           description=description,
                                           authors=authors,
                                           pageCount=pageCount,
                                           language=language,
                                           isbn=barcode,
                                           image=image)
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))


@app.route('/admin/store-book-db', methods=['POST'])
def storeBookAdminPost():
    try:
        # Database settings
        collection = db["books"]

        # Collect data
        title = request.form["title"]
        description = request.form["description"]
        image = request.form["imageLink"]
        authors = request.form["authors"]
        pageCount = request.form["pageCount"]
        language = request.form["language"]
        quantity = request.form["quantity"]
        isbn = request.form["isbn"]

        existingBook = collection.find_one({"isbn": isbn})

        if existingBook:
            print("yes")
            myquery = { "isbn": isbn }
            newQuantity = int(quantity)
            newvalues = { "$set": { "quantity": newQuantity } }
            collection.update_one(myquery, newvalues)
            return render_template('shared/halt-page.html', headerText="Redirecting", messageText="Successfully Updated Data into the Database", redirectLink="/admin/home")
        else:
            # Insert data
            collection.insert_one({
                "title": title,
                "description": description,
                "image": image,
                "authors": authors,
                "pageCount": int(pageCount),
                "language": language,
                "quantity": int(quantity),
                "isbn":int(isbn),
                "issuedBy": []
            })
            return render_template('shared/halt-page.html', headerText="Redirecting", messageText="Successfully Stored Data into the Database", redirectLink="/admin/home")

    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e))


# Error handling for 404 requests

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", headerText="Error 404", messageText="Couldn't find such route")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
