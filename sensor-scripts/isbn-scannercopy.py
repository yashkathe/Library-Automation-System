import serial
import time
import os
import RPi.GPIO as GPIO

# configure the serial port
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
# wait for the scanner to initialize
time.sleep(1)
GPIO.output(18, GPIO.HIGH)
while True:
    GPIO.output(18, GPIO.HIGH)
   #read the data from the serial port
    data = ser.read(13)
    
    #decode the barcode data
    barcode = data.decode('utf-8')
   #GPIO.output(18, GPIO.LOW)

    
    # print the barcode data
    print('Barcode:', barcode)
    #os._exit(os.EX_OK)


