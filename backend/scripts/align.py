import cv2
import numpy as np

MAX_FEATURES = 500
GOOD_MATCH_PERCENT = 0.11
AVG_MATCH_DIST_CUTOFF = 47 # lower cutoff is more strict


class AlignmentError(Exception):
    """Raised when alignment error is too high"""
    def __init__(self, msg):
        self.msg = msg


def align_images(im1, im2):
    """
    Args:
        im1 (numpy.ndarray): image to align
        im2 (numpy.ndarray): template image
    Returns:
        im1reg (numpy.ndarray): aligned version of im1
        im_matches (numpy.ndarray): debug image showing the common features used for alignment
        h (numpy.ndarray): matrix describing homography
        align_score (float): average max distance, lower is better
    """

    # Convert images to grayscale
    im_1_gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    im_2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

    # Detect ORB features and compute descriptors.
    orb = cv2.ORB_create(MAX_FEATURES)
    key_points_1, descriptors_1 = orb.detectAndCompute(im_1_gray, None)
    key_points_2, descriptors_2 = orb.detectAndCompute(im_2_gray, None)

    # Match features.
    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = matcher.match(descriptors_1, descriptors_2, None)

    # Sort matches by score
    matches.sort(key=lambda x: x.distance, reverse=False)

    # Remove not so good matches
    num_good_matches = int(len(matches) * GOOD_MATCH_PERCENT)
    matches = matches[:num_good_matches]

    # Validate the matches for quality
    match_distances = [m.distance for m in matches]
    avg_match_dist = np.mean(match_distances)
    if avg_match_dist > AVG_MATCH_DIST_CUTOFF:
        # Uncomment the lines below for console debug
        print(avg_match_dist)
        print(AVG_MATCH_DIST_CUTOFF)
        # print(avg_match_dist > AVG_MATCH_DIST_CUTOFF)
        raise AlignmentError("Poor image alignment! Please confirm you are using\n \
        the right form, and upload a new image.")

    # Draw top matches
    im_matches = cv2.drawMatches(im1, key_points_1, im2, key_points_2, matches, None)

    # Extract location of good matches
    points_1 = np.zeros((len(matches), 2), dtype=np.float32)
    points_2 = np.zeros((len(matches), 2), dtype=np.float32)

    for i, match in enumerate(matches):
        points_1[i, :] = key_points_1[match.queryIdx].pt
        points_2[i, :] = key_points_2[match.trainIdx].pt

    # Find homography
    try:
        h, mask = cv2.findHomography(points_1, points_2, cv2.RANSAC)
    except:
        raise AlignmentError("Inproper Homography in Alignment! Please confirm you are using\n \
        the right form, and upload a new image.")

    # Use homography
    height, width, channels = im2.shape
    im1Reg = cv2.warpPerspective(im1, h, (width, height))

    return im1Reg, im_matches, h, avg_match_dist
