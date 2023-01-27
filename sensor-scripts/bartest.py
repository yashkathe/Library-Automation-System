from pyzbar import pyzbar
import cv2
import argparse
from imutils.video import VideoStream
import time
import imutils
#Video stream

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())
#vs = VideoStream(src=0).start()  #Uncomment this if you are using Webcam
vs = VideoStream(usePiCamera=True).start() # For Pi Camera
time.sleep(0.1)
found = set()

#video stream

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    # decodes all barcodes from an image
    decoded_objects = pyzbar.decode(frame)
    for obj in decoded_objects:
        # draw the barcode
        image = draw_barcode(obj, frame)
        # print barcode type & data
        isbn=obj.data
        type1=obj.type
        print("Type:", type1)
        print("Data:", isbn)
        print()


def draw_barcode(decoded, image):
    # n_points = len(decoded.polygon)
    # for i in range(n_points):
    #     image = cv2.line(image, decoded.polygon[i], decoded.polygon[(i+1) % n_points], color=(0, 255, 0), thickness=5)
    # uncomment above and comment below if you want to draw a polygon and not a rectangle
    image = cv2.rectangle(image, (decoded.rect.left, decoded.rect.top),
                            (decoded.rect.left + decoded.rect.width, decoded.rect.top + decoded.rect.height),
                            color=(0, 255, 0),
                            thickness=5)
    return image



