#!/usr/bin/env python3

import sys
import argparse
import cv2
import numpy as np
import os.path

MAX_FEATURES = 500
GOOD_MATCH_PERCENT = 0.15


def alignImages(im1, im2):

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

  # Draw top matches
  im_matches = cv2.drawMatches(im1, key_points_1, im2, key_points_2, matches, None)

  # Extract location of good matches
  points_1 = np.zeros((len(matches), 2), dtype=np.float32)
  points_2 = np.zeros((len(matches), 2), dtype=np.float32)

  for i, match in enumerate(matches):
    points_1[i, :] = key_points_1[match.queryIdx].pt
    points_2[i, :] = key_points_2[match.trainIdx].pt

  # Find homography
  h, mask = cv2.findHomography(points_1, points_2, cv2.RANSAC)

  # Use homography
  height, width, channels = im2.shape
  im1Reg = cv2.warpPerspective(im1, h, (width, height))

  return im1Reg, im_matches, h

def read_image(image_path):
    return cv2.imread(image_path, cv2.IMREAD_COLOR)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('template', help='Template image')
  ap.add_argument('image', help='Image to align based on template')
  ap.add_argument('aligned_output', help='Name of aligned output file')
  ap.add_argument('matched_output', help='Name of matched feature debug file')
  args = ap.parse_args()

  # Read template image
  print("Reading template image at: ", args.template)
  im_template = cv2.imread(args.template, cv2.IMREAD_COLOR)

  # Read image to be aligned
  print("Reading image to align at: ", args.image);
  im = cv2.imread(args.image, cv2.IMREAD_COLOR)

  # Registered image will be stored in im_registered.
  # The estimated homography will be stored in h.
  print("Aligning images ...")
  im_registered, im_matches, h = alignImages(im, im_template)

  # Write aligned image to disk
  print("Saving aligned image at: " + args.aligned_output)
  print("Saving matched image at: " + args.matched_output)
  cv2.imwrite(args.matched_output, im_matches)
  cv2.imwrite(args.aligned_output, im_registered)

  # Print estimated homography
  print("Estimated homography : \n",  h)

if __name__ == '__main__':
    sys.exit(main())
