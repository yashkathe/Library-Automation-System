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
import imutils
import time
import serial
from mfrc522 import SimpleMFRC522
import env
from datetime import datetime

# DataBase config
cluster = MongoClient(env.MONGO_URI)
db = cluster["LibraryDB"]

# GPIO config
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Flask Settings
app = Flask(__name__)
app.secret_key = "XXt4FjJOkvMteX9YUu30f3cidxr3WbFv"
app.debug = True

# Home page route


@app.route("/")
def home():
    session["student"] = None
    session["admin"] = None
    session["isbn"] = None
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
                                       messageText="Place your Issue or Return QR Code in front of camera to login now",
                                       headerText="Student LOGIN",
                                       redirectLink="/student/auth/login",
                                       mode="DETECTED",
                                       haltTime=3000
                                       )
            elif i == 1:
                return render_template('shared/halt-page.html',
                                       messageText="Interact with IR sensor when you are ready with your QR code",
                                       headerText="Student Login",
                                       haltTime=1000
                                       )
            else:
                return render_template('shared/halt-page.html',
                                       messageText="Not IR sensor detected",
                                       headerText="ERROR",
                                       haltTime=4000
                                       )
    except Exception as e:
        vs = VideoStream(src=0).start()
        vs.stop()
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/")


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
                    # Check for type of QRcode(return or issue) and return accordingly
                    index = barcodeData.find('@')
                    if index != -1:
                        # For returning QR codes
                        i = barcodeData.index("@")
                        userBarcode = barcodeData[0:i]
                        isbn = barcodeData[i+1:len(barcodeData)]
                        print(userBarcode)
                        print(isbn)
                        user = collection.find_one(
                            {"_id": ObjectId(userBarcode)})
                        session["student"] = str(user["_id"])
                        session["isbn"] = isbn
                        return render_template('shared/shared-home.html', message=[
                            "Started Scanning",
                            "The ISBN will be scanned now"
                        ],
                            mode="DETECTED",
                            headerText="Returning Book",
                            redirectLink="/student/return-book-db")
                    else:
                        # For issuing QR codes
                        user = collection.find_one(
                            {"_id": ObjectId(barcodeData)})
                        print(user)
                        session["student"] = str(user["_id"])
                        return render_template('shared/shared-home.html', message=[
                            "Started Scanning",
                            "The ISBN will be scanned now"
                        ],
                            mode="DETECTED",
                            headerText="Issuing Book",
                            redirectLink="/student/issue-book-db")
    except Exception as e:
        vs = VideoStream(src=0).start()
        vs.stop()
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/")


@app.route("/student/issue-home")
def issueBook():
    try:
        sessionStudent = session["student"]
        if (sessionStudent):
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
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/student/auth/halt-page")


@app.route("/student/issue-book-db")
def issueBookDB():
    try:
        sessionStudent = session["student"]
        print(sessionStudent)
        if (sessionStudent):
            ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            time.sleep(1)

            while True:
                data = ser.read(13)
                barcode = data.decode('utf-8')
                if (barcode):
                    barcode = int(barcode)
                    break

            if (barcode):
                bookCollection = db["books"]
                userCollection = db["users"]
                existingBook = bookCollection.find_one(
                    {"isbn": barcode})
                if (existingBook):

                    # update book collection
                    myquery = {"isbn": existingBook["isbn"]}
                    updatedQuantity = int(existingBook["quantity"]) - 1
                    newvalues = {"$set": {"quantity": updatedQuantity}}

                    bookCollection.update_one(myquery, newvalues)
                    newvalues = {
                        "$push": {"issuedBy": {
                            "user": ObjectId(sessionStudent),
                            "time": datetime.today().strftime('%d %b %Y')
                        }}}

                    bookCollection.update_one(myquery, newvalues)

                    # update user collection
                    myquery = {"_id": ObjectId(session["student"])}
                    newvalues = {
                        "$push": {"booksIssued": {
                            "book": ObjectId(existingBook["_id"]),
                            "time": datetime.today().strftime('%d %b %Y')
                        }}}

                    userCollection.update_one(myquery, newvalues)

                    return render_template('shared/halt-page.html',
                                           headerText="Issuing Successful",
                                           messageText="Successfully Issued Your '" +
                                           existingBook["title"] + "' Book",
                                           redirectLink="/student/auth/halt-page",
                                           bookImage=existingBook["image"],
                                           haltTime=4000)
                else:
                    raise Exception("There is no such book in a databse")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/student/auth/halt-page")


@app.route("/student/return-home")
def returnBook():
    try:
        sessionStudent = session["student"]
        if (sessionStudent):
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
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/student/auth/halt-page")


@app.route("/student/return-book-db")
def returnBookDB():
    try:
        sessionStudent = session["student"]
        sessionISBN = session["isbn"]
        if (sessionStudent):
            ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            time.sleep(1)

            while True:
                data = ser.read(13)
                barcode = data.decode('utf-8')
                if (barcode):
                    barcode = int(barcode)
                    break

            if (barcode):
                if (int(barcode) == int(sessionISBN)):
                    bookCollection = db["books"]
                    userCollection = db["users"]
                    existingBook = bookCollection.find_one(
                        {"isbn": barcode})
                    if (existingBook):

                        # update book collection
                        myquery = {"isbn": existingBook["isbn"]}
                        updatedQuantity = int(existingBook["quantity"]) + 1
                        newvalues = {"$set": {"quantity": updatedQuantity}}
                        bookCollection.update_one(myquery, newvalues)
                        newvalues = {
                            "$pull": {"issuedBy": {
                                "user": ObjectId(sessionStudent)
                            }}}
                        bookCollection.update_one(myquery, newvalues, True)

                        # update user collection
                        myquery = {"_id": ObjectId(session["student"])}
                        newvalues = {
                            "$pull": {"booksIssued": {
                                "book": ObjectId(existingBook["_id"])
                            }}}
                        userCollection.update_one(myquery, newvalues, True)
                        return render_template('shared/halt-page.html',
                                               headerText="Return Successful",
                                               messageText="Successfully Returned Your '" +
                                               existingBook["title"] +
                                               "' Book",
                                               redirectLink="/student/auth/halt-page",
                                               bookImage=existingBook["image"],
                                               haltTime=5000)
                    else:
                        raise Exception("There is no such book in a databse")
                else:
                    raise Exception("There is no such book in a databse")
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/student/auth/halt-page")

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
                                       mode="DETECTED",
                                       haltTime=4000
                                       )
            elif i == 1:
                return render_template('shared/halt-page.html',
                                       messageText="Interact with IR sensor when you are ready with your login barcode",
                                       headerText="Admin Login",
                                       haltTime=1000
                                       )
            else:
                return render_template('shared/halt-page.html',
                                       messageText="Not IR sensor detected",
                                       headerText="ERROR",
                                       haltTime=3000
                                       )
    except Exception as e:
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/")


@app.route("/admin/auth/login")
def loginAdmin():
    try:
        # setup database

        collection = db["users"]

        # start pi camera for qr code scanning

        ap = argparse.ArgumentParser()
        ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                        help="path to output CSV file containing barcodes")
        vs = VideoStream(src=0).start()
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
                    if (user and user["isAdmin"] == True):
                        session["admin"] = barcodeData
                        return redirect(url_for("irSensorAdmin"))
                    else:
                        raise Exception("You are not authorised")
    except Exception as e:
        # Uncomment this if you are using Webcam
        vs = VideoStream(src=0).start()
        vs.stop()
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/admin/auth/halt-page")


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
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/admin/auth/halt-page")


@app.route("/admin/store-book")
def storeBookAdmin():
    try:
        sessionAdmin = session["admin"]
        if (sessionAdmin):
            barcode = None
            ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            # wait for the scanner to initialize
            time.sleep(1)
            while True:
                data = ser.read(13)
                barcode = data.decode('utf-8')
                print('Barcode:', barcode)
                if barcode:
                    break
            if (barcode):
                # check if book with similar isbn exists
                collection = db["books"]
                existingBook = collection.find_one(
                    {"isbn": int(barcode)})
                # if similar book exists
                if (existingBook):
                    newAuthors = '%s' % ', '.join(
                        map(str, existingBook['authors']))
                    print(existingBook['authors'])
                    print(newAuthors)
                    return render_template('admin/store-book.html',
                                           headerText="Store Book Data into Database",
                                           title=existingBook['title'],
                                           description=existingBook['description'],
                                           authors=newAuthors,
                                           pageCount=existingBook['pageCount'],
                                           language=existingBook['language'],
                                           quantity=existingBook['quantity'],
                                           image=existingBook['image'],
                                           isbn=barcode,
                                           showBox="yes",
                                           quantityLabel="New Quantity"
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
                # If isbn for new book is scanned
                print(obj["items"][0])
                volume_info = obj["items"][0]
                author = obj["items"][0]["volumeInfo"]["authors"]
                authors = '%s' % ', '.join(map(str, author))
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
                                       image=image,
                                       quantityLabel="Quantity"
                                       )
        else:
            raise Exception("No Sessions found. Please login first")
    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/admin/auth/halt-page")


@app.route('/admin/store-book-db', methods=['POST'])
def storeBookAdminPost():
    try:
        # String to Array function for author
        def stringToArray(inputString):
            string_with_commas = inputString
            array_with_commas = string_with_commas.split(",")
            return array_with_commas

        # Database settings
        collection = db["books"]

        # Collect data
        title = request.form["title"]
        description = request.form["description"]
        image = request.form["imageLink"]
        author = request.form["authors"]
        pageCount = request.form["pageCount"]
        language = request.form["language"]
        quantity = request.form["quantity"]
        isbn = request.form["isbn"]

        # Modify Data
        isbn = int(isbn)
        pageCount = int(pageCount)
        quantity = int(quantity)
        authors = stringToArray(author)

        existingBook = collection.find_one({"isbn": isbn})
        print("authors1", authors)
        print("type1", type(authors))

        if existingBook:
            newQuantity = existingBook["quantity"] + quantity
            # Insert data for exisitng book
            myquery = {"isbn": isbn}
            newvalues = {"$set": {"quantity": newQuantity}}
            collection.update_one(myquery, newvalues)
            return render_template('shared/halt-page.html',
                                   headerText="Choose an option",
                                   messageText="Successfully Updated Data into the Database",
                                   redirectLink="/admin/home",
                                   extraButtons="TRUE",
                                   haltTime=5000)
        else:
            # Insert data for new Book
            print("authors2", authors)
            print("type2", type(authors))
            collection.insert_one({
                "title": title,
                "description": description,
                "image": image,
                "authors": authors,
                "pageCount": pageCount,
                "language": language,
                "quantity": quantity,
                "isbn": isbn,
                "issuedBy": []
            })
            return render_template('shared/halt-page.html',
                                   headerText="Choose an option",
                                   messageText="Successfully Stored Data into the Database",
                                   redirectLink="/admin/home",
                                   extraButtons="TRUE",
                                   haltTime=5000)

    except Exception as e:
        print(e)
        return render_template("error.html", headerText="Error", messageText=str(e), errorRoute="/admin/auth/halt-page")


# Error handling for 404 requests

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", headerText="Error 404", messageText="Couldn't find such route", errorRoute="/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
