import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)         #Read output from PIR motion sensor
#GPIO.setup(3, GPIO.OUT)         #LED output pin
while True:
    i=GPIO.input(11)
    if i==0:                 #When output from motion sensor is LOW
        print (i)
        #  #Turn OFF LED
        time.sleep(0.1) 
    elif i==1:               #When output from motion sensor is HIGH
        print (i)
        # #Turn ON LED
        time.sleep(0.1)
