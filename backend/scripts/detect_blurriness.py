import cv2
import numpy as np

# TODO: compare the amount of blur versus the template image bluriness
BLUR_THRESHOLD_MAX = -11  # lower is better, TODO: test with more images
BLUR_THRESHOLD_MIN = -200  # if the image is skewed/too low, something went wrong

def variance_of_laplacian(grayscale_image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(grayscale_image, cv2.CV_64F).var()

def blurry_score(image):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# make score negative to align with alignment score, where lower is better
	return -variance_of_laplacian(gray)

def is_blurry(score):
    return score < BLUR_THRESHOLD_MIN or score > BLUR_THRESHOLD_MAX

def compute_blurriness(image):
    # Takes in an image and returns a Tuple of (is_blurry, blurry_score)
    score = blurry_score(image)
    return is_blurry(score), score
