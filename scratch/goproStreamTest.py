import cv2
import numpy as np
from goprocam import GoProCamera
from goprocam import constants

import numpy as np
import cv2

cap = cv2.VideoCapture(1)

iterval = 0
while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame', gray)
    if iterval <= 111:
        cv2.imwrite("test" + str(iterval) + ".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, 90])
        iterval += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

#
# # cascPath="/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml"
# # faceCascade = cv2.CascadeClassifier(cascPath)
# gpCam = GoProCamera.GoPro()
# print("here")
# cap = cv2.VideoCapture("udp://127.0.0.1:10000")
# if not cap.isOpened():
#     print('VideoCapture not opened')
#     exit(-1)
#
# print("here1")
# while True:
#     print("here2")
#     ret, frame = cap.read()
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     # faces = faceCascade.detectMultiScale(
#     #     gray,
#     #     scaleFactor=1.1,
#     #     minNeighbors=5,
#     #     minSize=(30, 30),
#     #     flags=cv2.CASCADE_SCALE_IMAGE
#     # )
#     # for (x, y, w, h) in faces:
#     #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#     cv2.imshow("GoPro OpenCV", frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
# cap.release()
# cv2.destroyAllWindows()
