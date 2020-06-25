# import the necessary packages
from threading import Thread
import threading
import numpy as np
import cv2
import time


class Camera:
	def __init__(self, src=0, name="Camera"):
		# Initialize the video camera stream
		cap = cv2.VideoCapture(src)
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, 11111)
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 11111)
		self.stream = cap

		# Test and Display Initial camera image quality.
		(_, test_frame) = self.stream.read()
		self.width_quality, self.height_quality, _  = test_frame.shape
		print("Camera Image Quality: %i x %i" % (self.width_quality, self.height_quality))

		# Initialize local variables
		self.name = name # Camera object name
		self.frame = np.zeros((1,1,1)) # Current frame
		self.stopped = True # Manages camera state

	def start(self):
		self.stopped = False
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, name=self.name, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			time.sleep(.1)

			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			(_, self.frame) = self.stream.read()

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.frame = np.zeros((1,1,1)) # Current frame
		self.stopped = True

	def close_hardware_connection(self):
		# Close the connection to the camera hardware
		self.stop()
		self.stream.release()

	def stream_quality_preserved(self):
		# Check if the given width and height are greater than or equal to
		# the quality at the time of origination. If not, return False
		current_width, current_height, _ = self.frame.shape
		print("Image Quality: %i x %i" % (current_width, current_height))
		return ((current_width >= self.width_quality) or (current_height >= self.height_quality))
