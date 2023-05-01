ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(1)

while True:
    data = ser.read(13)    
    barcode = data.decode('utf-8')    
