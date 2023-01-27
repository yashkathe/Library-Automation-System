from pyzbar import pyzbar
import cv2

def decode(image):
    # decodes all barcodes from an image
    decoded_objects = pyzbar.decode(image)
    for obj in decoded_objects:
        # draw the barcode
        image = draw_barcode(obj, image)
        # print barcode type & data
        isbn=obj.data
        type1=obj.type
        print("Type:", type1)
        print("Data:", isbn)
        print()
        return image, isbn, type1


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

# load the image to opencv
image = cv2.imread("test1.jpg")
# decode detected barcodes & get the image
# that is drawn
image = decode(image)
# show the image
cv2.imshow("img", image)
#cv2.waitKey(0)
