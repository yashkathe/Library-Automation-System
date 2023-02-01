from PIL import Image
import pyzbar.pyzbar as pyzbar
from picamera import Picamera
camera = Picamera()

# Use the Raspberry Pi camera to capture an image
# and save it to a file
camera.capture("barcode.jpg")

# Open the image file using PIL
im = Image.open("barcode.jpg")

# Decode the barcode in the image
barcodes = pyzbar.decode(im)

# Print the decoded ISBN-13 number
for barcode in barcodes:
    if barcode.type == "EAN13":
        print("ISBN-13:", barcode.data.decode("utf-8"))
