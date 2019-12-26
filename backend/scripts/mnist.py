# import numpy as np
# import onnxruntime as rt
# import math
# import cv2
# from scipy import ndimage
# from pathlib import Path
#
# _digit_val = 0
# debug = False
#
# def write_prediction(image, argmax):
#     global _digit_val
#     cv2.imwrite("./_digit_input_" + str(_digit_val) + "_predict_" + str(argmax) + ".png", image)
#     _digit_val += 1
#
# # Takes in an image and returns a tuple of (predicted digit, probability)
# def predict_digit(image):
#     processed_image = mnist_preprocess(image)
#
#     # currently uses a pretrained model and ONNX runtime to do inference
#     model = getOrInitializeModel()
#     input_name = model.get_inputs()[0].name
#     pred_onnx = model.run(None, {input_name: processed_image})
#     probabilities = softmax(pred_onnx[0][0])
#     argmax = probabilities.argmax()
#     if debug:
#         write_prediction(image, argmax)
#     return (argmax, probabilities[argmax])
#
# def getBestShift(img):
#     cy,cx = ndimage.measurements.center_of_mass(img)
#
#     rows,cols = img.shape
#     shiftx = np.round(cols / 2.0 - cx).astype(int)
#     shifty = np.round(rows / 2.0 - cy).astype(int)
#
#     return shiftx, shifty
#
# def shift(img, sx, sy):
#     rows, cols = img.shape
#     M = np.float32([[1, 0, sx],[0, 1, sy]])
#     shifted = cv2.warpAffine(img, M, (cols, rows))
#     return shifted
#
# # Preprocessing steps mostly taken from
# # https://medium.com/@o.kroeger/tensorflow-mnist-and-your-own-handwritten-digits-4d1cd32bbab4
# # I also normalized the data to follow the MNIST training data distribution,
# # and removed the step to remove the border of an image since for now i assume
# # there isn't one.
#
# # takes in an (image address, optional write address) returns numpy [1, 1, 28, 28] tensor
#
# def mnist_preprocess(image):
#     # rescale it
#     image = cv2.resize(255 - image, (28, 28))
#
#     max = np.max(image)
#     # TODO: refine edge cutoff technique / percentage
#     EDGE_CUTOFF_PERCENT = .65
#     cutoff = max * EDGE_CUTOFF_PERCENT
#
#     while np.mean(image[0]) > cutoff:
#       image = image[1:]
#
#     while np.mean(image[:,0]) > cutoff:
#       image = np.delete(image, 0, 1)
#
#     while np.mean(image[-1]) > cutoff:
#       image = image[:-1]
#
#     while np.mean(image[:,-1]) > cutoff:
#       image = np.delete(image, -1, 1)
#
#     # better black and white version
#     (thresh, grayscale_image) = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
#
#     rows, cols = grayscale_image.shape
#
#     if rows > cols:
#       factor = 20.0 / rows
#       rows = 20
#       cols = int(round(cols*factor))
#       # first cols than rows
#       grayscale_image = cv2.resize(grayscale_image, (cols,rows))
#     else:
#       factor = 20.0 / cols
#       cols = 20
#       rows = int(round(rows * factor))
#       # first cols than rows
#       grayscale_image = cv2.resize(grayscale_image, (cols, rows))
#
#     colsPadding = (int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
#     rowsPadding = (int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
#     grayscale_image = np.lib.pad(grayscale_image, (rowsPadding , colsPadding), 'constant')
#
#     shiftx, shifty = getBestShift(grayscale_image)
#     grayscale_image = shift(grayscale_image, shiftx, shifty)
#
#     grayscale_image = grayscale_image / 255.0
#     grayscale_image = np.float32(grayscale_image)
#
#     MNIST_TRAINING_MEAN = 0.1307
#     MNIST_TRAINING_STD = 0.3081
#
#     # normalize data distribution to follow MNIST
#     # see https://discuss.pytorch.org/t/normalization-in-the-mnist-example/457
#     grayscale_image = (grayscale_image - MNIST_TRAINING_MEAN) / MNIST_TRAINING_STD
#
#     # trained mnist model 4-D inputs due to batching
#     grayscale_image.resize([1, 1, 28, 28])
#     return grayscale_image
#
# # pretrained MNIST model taken from
# # https://github.com/onnx/models/tree/master/vision/classification/mnist
# # Accuracy when I tested it against MNIST dataset was .984
# # There are certainly models that test with a higher accuracy, however
# # I think probably a bigger limitation in our pipeline be will digit quality
# # and preprocessing
#
# # TODO - relative path to digitize-mtc
# MODEL_ADDRESS = Path.cwd() / "backend/scripts/model.onnx"
# mnist_model = None
#
# def getOrInitializeModel():
#     global mnist_model
#     if mnist_model is None:
#         mnist_model = rt.InferenceSession(str(MODEL_ADDRESS))
#     return mnist_model
#
# def softmax(x):
#     """Compute softmax values for each sets of scores in x."""
#     e_x = np.exp(x - np.max(x))
#     return e_x / e_x.sum(axis = 0)
