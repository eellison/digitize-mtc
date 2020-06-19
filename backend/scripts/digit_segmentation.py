import cv2
import numpy as np

def get_minima_maxima(apprx):
    assert len(apprx) == 4
    x_vals = apprx[:, 0, 0]
    y_vals = apprx[:, 0, 1]
    return np.amin(x_vals), np.amax(x_vals), np.amin(y_vals), np.amax(y_vals)


# this filters contours that are contained within another contour.
# this can occur with any digit that forms a rectangular contour within a digit box
def filter_contained_contours(apprx_contours):
    res = []
    for i in range(len(apprx_contours)):
        apprx_i = apprx_contours[i]
        min_x, max_x, min_y, max_y = get_minima_maxima(apprx_i)
        in_interval = False

        for j in range(len(apprx_contours)):
            if i == j:
                continue
            apprx_j = apprx_contours[j]
            min_x_j, max_x_j, min_y_j, max_y_j = get_minima_maxima(apprx_j)
            x_contained = min_x_j < min_x and max_x_j > max_x
            y_contained = min_y_j < min_y and max_y_j > max_y

            if x_contained and y_contained:
                in_interval = True
                break
        if not in_interval:
            res.append(apprx_i)
    return res

def filter_outlier_size(apprx_contours):
    if len(apprx_contours) == 0:
        return []

    total_area = 0.
    apprx_area = []
    for apprx in apprx_contours:
        min_x, max_x, min_y, max_y = get_minima_maxima(apprx)
        area = (max_x - min_x) * (max_y - min_y)
        apprx_area.append(area)
        total_area += area

    avg_area = total_area / len(apprx_contours)
    res = []
    for i in range(len(apprx_contours)):
        # this mostly catches very small things, so we're lenient on the
        # percentage difference. if larger things pop up, rethink the process
        MAX_PERCENT_DIFF = .5
        percent_diff = apprx_area[i] / avg_area
        if (percent_diff < MAX_PERCENT_DIFF or percent_diff > (1 / MAX_PERCENT_DIFF)):
            continue
        res.append(apprx_contours[i])
    return res


def filter_contours(apprx_contours):
    apprx_contours = filter_contained_contours(apprx_contours)
    return filter_outlier_size(apprx_contours)

def sort_contours(apprx_contours):
    def x_min(val):
        x_min, _, _, _ = get_minima_maxima(val)
        return x_min

    apprx_contours.sort(key=x_min)
    return apprx_contours

def extract_images(img, approx_contours):
    res = []
    for approx in approx_contours:
        min_x, max_x, min_y, max_y = get_minima_maxima(approx)
        out = img[min_y: max_y, min_x:max_x]
        res.append(out)
    return res

def extract_digit_boxes(image):
    # adapted from https://www.quora.com/How-I-detect-rectangle-using-OpenCV
    _, thresh = cv2.threshold(image, 127, 255, 1)
    contours, h = cv2.findContours(thresh, 1, 2)

    rectangles = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            rectangles.append(approx)

    filtered = filter_contours(rectangles)
    sorted = sort_contours(filtered)
    return extract_images(image, sorted)
