import cv2
import sys
sys.path.append("..") # Adds higher directory to python modules path so we can import
import os
from scripts import predict_digit

def predict_from_image_address(image_address):
    grayscale_image = cv2.imread(image_address, 0)
    assert grayscale_image is not None, "Could not read image address: {}".format(image_address)
    return predict_digit(grayscale_image)

def test():

    # these are digits taken from a scanned filled out form, so they should be
    # somewhat accurate to what we will receive.
    # currently the border of the digit grid is cropped out
    images = [
        ("zero_screenshot.png", 0),
        ("one_screenshot.png", 1),
        ("two_screenshot.png", 2),
        ("three_screenshot.png", 3),
    ]

    num_predicted = 0
    for image_name, expected_digit in images:
        image_path = os.path.abspath("./mnist_digits/" + image_name)
        prediction, prob = predict_from_image_address(image_path)

        # we should either have the prediction right or have low confidence
        assert prediction == expected_digit or prob <= .8
        num_predicted += (prediction == expected_digit)

    print("{predicted} predicted out of {total}".format(predicted=num_predicted, total=len(images)))

if __name__ == "__main__":
    test()
