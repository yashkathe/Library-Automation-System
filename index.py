from flask import Flask, render_template
import RPi.GPIO as GPIO
from pymongo import MongoClient
import os

cluster = MongoClient(os.environ.get("MONGO_URI"))
db = cluster["LibraryDB"]
collection = db["users"]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

app = Flask(__name__)
app.debug = True

# Home page route


@app.route("/")
def home():
    return render_template('home.html')

# Student pages route


@app.route("/student/home")
def irSensor():
    GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor
    while True:
        i = GPIO.input(11)
        if i == 0:  # When output from motion sensor is HIGH
            return render_template('student-home.html', message=[
                "Student detected",
                "Place your barcode in front of the camera"
            ],
                mode="DETECTED")
        elif i == 1:
            return render_template('student-home.html', message=[
                "No Student detected"],
                mode="NOTDETECTED")
        else:
            return render_template('student-home.html', message=[
                "PIR sensor is not connected to the system"],
                mode="ERROR")


@app.route("/student/QRlogin")
def qrLogin():
    post = {"email": "yash123", "pid": "123", "password": "123"}
    collection.insert_one(post)
    return render_template('qrlogin.html')

# Admin pages route


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
