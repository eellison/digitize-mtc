import cv2
import numpy as np
from .util import *

MAX_FEATURES = 5000
GOOD_MATCH_PERCENT = 0.22
AVG_MATCH_DIST_CUTOFF = 47 # lower cutoff is more strict


class AlignmentError(Exception):
	"""Raised when alignment error is too high"""
	def __init__(self, msg):
		self.msg = msg


def global_align(im1, im2):
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

	assert isinstance(im1, np.ndarray) and isinstance(im2, np.ndarray)

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
	avg_match_dist = np.median(match_distances)
	# if avg_match_dist > AVG_MATCH_DIST_CUTOFF:
	#     # Uncomment the lines below for console debug
	#     print(avg_match_dist)
	#     print(AVG_MATCH_DIST_CUTOFF)
	#     # print(avg_match_dist > AVG_MATCH_DIST_CUTOFF)
	#     raise AlignmentError("Poor image alignment! Please confirm you are using\n \
	#     the right form, and upload a new image.")

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
	im1_warp = cv2.warpPerspective(im1, h, (width, height))

	###  Check homography for improvement ###
	im1_warp_gray = cv2.cvtColor(im1_warp, cv2.COLOR_BGR2GRAY)
	key_points_warp, descriptors_warp = orb.detectAndCompute(im1_warp_gray, None)
	matches_warp = matcher.match(descriptors_warp, descriptors_2, None)
	# Sort matches by score
	matches_warp.sort(key=lambda x: x.distance, reverse=False)
	matches_warp = matches_warp[:num_good_matches]
	# Validate the matches for quality
	match_distances_warp = [m.distance for m in matches_warp]
	avg_match_dist_warp = np.median(match_distances_warp)

	print("Average match dist:")
	print(avg_match_dist)
	print("Average match dist warp:")
	print(avg_match_dist_warp)

	if (avg_match_dist > AVG_MATCH_DIST_CUTOFF) or (avg_match_dist_warp > avg_match_dist): # or
		# The perspective warp reduced the average match quality OR "the original image was shit" -Dan
		# cv2.imwrite("original_bad.jpg", im1)
		# cv2.imwrite("warped_bad.jpg", im1_warp)
		raise AlignmentError("Poor image alignment! Please confirm you are using\n \
		the right form, and upload a new image.")

	# cv2.imwrite("original_good.jpg", im1)
	# cv2.imwrite("warped_good.jpg", im1_warp)

	return im1_warp, im_matches, h, avg_match_dist


def local_align(im1, im2, form):
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
	project_mark_locations(im2[:,:,0], form)
	im_aligned = np.zeros_like(im2, dtype=np.uint8)

	for group in form.question_groups:

		# Get question group
		w, h, x, y = (group.w, group.h, group.x, group.y)
		im1_quad = im1[y:y+h, x:x+w,:]
		im2_quad = im2[y:y+h, x:x+w,:]

		# Convert images to grayscale
		im_1_gray = cv2.cvtColor(im1_quad, cv2.COLOR_BGR2GRAY)
		im_2_gray = cv2.cvtColor(im2_quad, cv2.COLOR_BGR2GRAY)

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

		# Extract location of good matches
		points_1 = np.zeros((len(matches), 2), dtype=np.float32)
		points_2 = np.zeros((len(matches), 2), dtype=np.float32)

		for i, match in enumerate(matches):
			points_1[i, :] = key_points_1[match.queryIdx].pt
			points_2[i, :] = key_points_2[match.trainIdx].pt

		# Find homography
		try:
			homography, mask = cv2.findHomography(points_1, points_2, cv2.RANSAC)
		except:
			raise AlignmentError("Inproper Homography in Alignment! Please confirm you are using\n \
			the right form, and upload a new image.")

		# Use homography
		height, width, _ = im2_quad.shape
		im_warp = cv2.warpPerspective(im1_quad, homography, (width, height))
		im_aligned[y:y+h, x:x+w,:] = im_warp

	return im_aligned



def finetune(input_image, template_image, response_region):
	"""
	Args:
		input_image (numpy.ndarray): target image
		template_image (numpy.ndarray): template image
		response_region (ResponseRegion): describes location of checkbox
	Returns:
		mutates response region x and y attritibute to account for translation
	"""
	alpha = 0.5
	w, h, x, y = (response_region.w, response_region.h, response_region.x, response_region.y)
	x_offset, y_offset = int(alpha * w), int(alpha * h)
	crop = template_image[max(0,y-y_offset//2) : y+h+y_offset//2, max(0,x-x_offset//2) : x+w+x_offset//2]#[y:y+h, x:x+w]
	ref = input_image[max(0,y-y_offset) : y+h+y_offset, max(0,x-x_offset) : x+w+x_offset]

	res = cv2.matchTemplate(crop, ref, cv2.TM_CCOEFF_NORMED)
	_, _, min_loc, max_loc = cv2.minMaxLoc(res)

	fpl = 5 # finetune pixel limit

	finetune_x = max_loc[0] - x_offset//2
	finetune_y = max_loc[1] - y_offset//2

	print(response_region.name)
	print(finetune_x, finetune_y)

	# Finetune response region coordinates, within pixel limit
	response_region.x += max(-fpl, min(finetune_x, fpl))
	response_region.y += max(-fpl, min(finetune_y, fpl))
