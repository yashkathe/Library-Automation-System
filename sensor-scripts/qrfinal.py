from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import imutils
import time
import cv2
import os

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())
#vs = VideoStream(src=0).start()  #Uncomment this if you are using Webcam
vs = VideoStream(usePiCamera=True).start() # For Pi Camera
time.sleep(0.1)
found = set()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
	#barcodeData holds the value for qrcode 
        print (barcodeData) 
        os._exit(os.EX_OK)
        cv2.putText(frame, text, (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

#if the barcode text is currently not in our CSV file, write
#the timestamp + barcode to disk and update the set
#if barcodeData not in found:
#    found.add(barcodeData)
#    cv2.imshow("Barcode Reader", frame)
#    key = cv2.waitKey(1) & 0xFF

# if the `s` key is pressed, break from the loop
#if key == ord("s"):
#    print("[INFO] cleaning up...")
#    csv.close()
#    cv2.destroyAllWindows()
