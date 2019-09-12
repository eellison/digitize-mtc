import numpy as np
# import onnxruntime as rt
import math
import cv2
from scipy import ndimage
from pathlib import Path

# Takes in a image address and returns a tuple of (predicted digit, probability)
def predict_digit(image):
    processed_image = mnist_preprocess(image)

    # currently uses a pretrained model and ONNX runtime to do inference
    model = getOrInitializeModel()
    input_name = model.get_inputs()[0].name
    pred_onnx = model.run(None, {input_name: processed_image})
    probabilities = softmax(pred_onnx[0][0])
    argmax = probabilities.argmax()
    # import pdb; pdb.set_trace()
    return (argmax, probabilities[argmax])


def getBestShift(img):
    cy,cx = ndimage.measurements.center_of_mass(img)

    rows,cols = img.shape
    shiftx = np.round(cols / 2.0 - cx).astype(int)
    shifty = np.round(rows / 2.0 - cy).astype(int)

    return shiftx, shifty

def shift(img, sx, sy):
    rows, cols = img.shape
    M = np.float32([[1, 0, sx],[0, 1, sy]])
    shifted = cv2.warpAffine(img, M, (cols, rows))
    return shifted

# Preprocessing steps mostly taken from
# https://medium.com/@o.kroeger/tensorflow-mnist-and-your-own-handwritten-digits-4d1cd32bbab4
# I also normalized the data to follow the MNIST training data distribution,
# and removed the step to remove the border of an image since for now i assume
# there isn't one.

# takes in an (image address, optional write address) returns numpy [1, 1, 28, 28] tensor

def mnist_preprocess(image_address, debug_out_file=None):
    # read the image
    grayscale_image = cv2.imread(image_address, 0)
    assert grayscale_image is not None, "Could not read image address: {}".format(image_address)

    # rescale it
    grayscale_image = cv2.resize(255 - grayscale_image, (28, 28))
    # better black and white version
    (thresh, grayscale_image) = cv2.threshold(grayscale_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # TODO: Erase borders when they are included in the image and improve cropping below
    # For now assume not present,
    # while np.sum(gray[0]) == 0:
    #   gray = gray[1:]
    #
    # while np.sum(gray[:,0]) == 0:
    #   gray = np.delete(gray,0,1)
    #
    # while np.sum(gray[-1]) == 0:
    #   gray = gray[:-1]
    #
    # while np.sum(gray[:,-1]) == 0:
    #   gray = np.delete(gray,-1,1)

    rows, cols = grayscale_image.shape

    if rows > cols:
      factor = 20.0 / rows
      rows = 20
      cols = int(round(cols*factor))
      # first cols than rows
      grayscale_image = cv2.resize(grayscale_image, (cols,rows))
    else:
      factor = 20.0 / cols
      cols = 20
      rows = int(round(rows * factor))
      # first cols than rows
      grayscale_image = cv2.resize(grayscale_image, (cols, rows))

    colsPadding = (int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
    rowsPadding = (int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
    grayscale_image = np.lib.pad(grayscale_image, (rowsPadding , colsPadding), 'constant')

    shiftx, shifty = getBestShift(grayscale_image)
    grayscale_image = shift(grayscale_image, shiftx, shifty)
    grayscale_image = grayscale_image / 255.0
    grayscale_image = np.float32(grayscale_image)

    MNIST_TRAINING_MEAN = 0.1307
    MNIST_TRAINING_STD = 0.3081

    # normalize data distribution to follow MNIST
    # see https://discuss.pytorch.org/t/normalization-in-the-mnist-example/457
    grayscale_image = (grayscale_image - MNIST_TRAINING_MEAN) / MNIST_TRAINING_STD

    if debug_out_file:
        cv2.imwrite(debug_out_file, grayscale_image)

    # trained mnist model 4-D inputs due to batching
    grayscale_image.resize([1, 1, 28, 28])
    return grayscale_image

# pretrained MNIST model taken from
# https://github.com/onnx/models/tree/master/vision/classification/mnist
# Accuracy when I tested it against MNIST dataset was .984
# There are certainly models that test with a higher accuracy, however
# I think probably a bigger limitation in our pipeline be will digit quality
# and preprocessing

# TODO - relative path to digitize-mtc
MODEL_ADDRESS = Path.cwd().parent / "scripts/model.onnx"
mnist_model = None

def getOrInitializeModel():
    global mnist_model
    if mnist_model is None:
        mnist_model = rt.InferenceSession(str(MODEL_ADDRESS))
    return mnist_model

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis = 0)
