import serial
import time
import os

# configure the serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# wait for the scanner to initialize
time.sleep(1)

while True:
    # read the data from the serial port
    data = ser.read(13)
    
    # decode the barcode data
    barcode = data.decode('utf-8')
    
    # print the barcode data
    print('Barcode:', barcode)
    os._exit(os.EX_OK)


