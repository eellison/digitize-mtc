import cv2
import numpy as np
from .util import *

MAX_FEATURES = 5000
GOOD_MATCH_PERCENT = 0.22
AVG_MATCH_DIST_CUTOFF = 47 # Lower cutoff is more strict
FPL = 5 # Finetune pixel limit; max number of pixels to finetune region locations


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

	# 1) Compute feature matches between template and input image
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

	# 2) Validate the matches for quality
	match_distances = [m.distance for m in matches]
	avg_match_dist = np.median(match_distances)
	if avg_match_dist > AVG_MATCH_DIST_CUTOFF:
	    # Write the alignment score to console:
	    print("Average match distance of %d exceeds match distance cutoff of %d." \
			% (avg_match_dist, AVG_MATCH_DIST_CUTOFF))
	    raise AlignmentError("GLOBAL ALIGNMENT WARNING: Poor image alignment!\n\
	    Please confirm you are using the right form, and upload a new image.")

	# 3) Use the matches to compute + apply the homography
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
		raise AlignmentError("GLOBAL ALIGNMENT WARNING: Inproper Homography in Alignment!\n \
		Please confirm you are using the right form, and upload a new image.")
	# Use homography
	height, width, channels = im2.shape
	im1_warp = cv2.warpPerspective(im1, h, (width, height))

	# 4) Check homography for improvement
	im1_warp_gray = cv2.cvtColor(im1_warp, cv2.COLOR_BGR2GRAY)
	key_points_warp, descriptors_warp = orb.detectAndCompute(im1_warp_gray, None)
	matches_warp = matcher.match(descriptors_warp, descriptors_2, None)
	# Sort matches by score
	matches_warp.sort(key=lambda x: x.distance, reverse=False)
	matches_warp = matches_warp[:num_good_matches]
	# Validate the matches for quality
	match_distances_warp = [m.distance for m in matches_warp]
	avg_match_dist_warp = np.median(match_distances_warp)
	if avg_match_dist_warp > avg_match_dist: 
		# The perspective warp reduced the average match quality OR "the original image was shit" -Dan
		raise AlignmentError("Poor image alignment! Applying homography reduced \n \
		the alignment score. Please confirm camera image quality.")

	return im1_warp, im_matches, h, avg_match_dist


def local_align(im1, im2, form):
	"""
	Aligns each question group of the form individually, and puts all of the regions
	together for final output 
	Args:
		im1 (numpy.ndarray): image to align
		im2 (numpy.ndarray): template image
	Returns:
		im_aligned (numpy.ndarray): locally aligned version of im1
	"""

	# Project mark locations from template onto input image
	project_mark_locations(im2[:,:,0], form)
	# Initialize an empty numpy array to fill in with locally aligned regions
	im_aligned = np.zeros_like(im2, dtype=np.uint8)
	# Loop through every question group and align the corresponding regions of
	# im1 and im2 
	for group in form.question_groups:
		# Get question group regions
		w, h, x, y = (group.w, group.h, group.x, group.y)
		im1_region = im1[y:y+h, x:x+w,:]
		im2_region = im2[y:y+h, x:x+w,:]
		# Align the two regions using the global_align funciton
		try:
			(im_warp, _, _, _) = global_align(im1_region, im2_region)
		except AlignmentError:
			raise AlignmentError("GLOBAL ALIGNMENT WARNING: Error in Local Alignment.")
		# Write the aligned region into the final output image
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
	crop = template_image[max(0,y-y_offset//2) : y+h+y_offset//2, max(0,x-x_offset//2) : x+w+x_offset//2]
	ref = input_image[max(0,y-y_offset) : y+h+y_offset, max(0,x-x_offset) : x+w+x_offset]

	res = cv2.matchTemplate(crop, ref, cv2.TM_CCOEFF_NORMED)
	_, _, min_loc, max_loc = cv2.minMaxLoc(res)

	# Compute the number of pixes to finetune in the x and y dimensions
	finetune_x = max_loc[0] - x_offset//2
	finetune_y = max_loc[1] - y_offset//2
	# Finetune response region coordinates, within pixel limit
	# I.e. finetune_x or finetune_y exceed FPL, adjust by FPL. This avoids gross adjustments
	# in the location of checkboxes at this stage in the alignment process. 
	response_region.x += max(-FPL, min(finetune_x, FPL))
	response_region.y += max(-FPL, min(finetune_y, FPL))
