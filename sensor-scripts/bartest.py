import cv2
from pyzbar import pyzbar

#initialize the camera
camera = cv2.VideoCapture(0)

while True:
    #grab the current frame
    ret, frame = camera.read()

    #decode the barcode
    decoded_objects = pyzbar.decode(frame)
   
    #loop over the decoded objects
    for obj in decoded_objects:
        #extract the bounding box location of the barcode
	image = draw_barcode(obj, frame)
        # print barcode type & data
        isbn=obj.data
        type1=obj.type
        print("Type:", type1)
        print("Data:", isbn)
        print()


def draw_barcode(decoded, frame):
    # n_points = len(decoded.polygon)
    # for i in range(n_points):
    #     image = cv2.line(image, decoded.polygon[i], decoded.polygon[(i+1) % n_points], color=(0, 255, 0), thickness=5)
    # uncomment above and comment below if you want to draw a polygon and not a rectangle
    image = cv2.rectangle(frame, (decoded.rect.left, decoded.rect.top),
                            (decoded.rect.left + decoded.rect.width, decoded.rect.top + decoded.rect.height),
                            color=(0, 255, 0),
                            thickness=5)
    return frame

    #show the frame
    cv2.imshow("Barcode scanner", frame)

    #if the 'q' key is pressed, stop the loop
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

#cleanup
camera.release()
cv2.destroyAllWindows()
