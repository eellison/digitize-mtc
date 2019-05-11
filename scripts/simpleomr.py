#!/usr/bin/env python3

import argparse
import sys
import re

from PIL import Image, ImageDraw, ImageOps
from skimage.filters import threshold_local
from enum import Enum
import numpy as np
import scipy as sp
import scipy.ndimage
import lxml.etree


# tuned for 300 dpi grayscale text
BLACK_LEVEL  = 0.5 * 255
FILL_THR     = 0.11 # threshold for filled box
CHECK_THR    = 0.04 # threshold for checked box
EMPTY_THR    = 0.02 # threashold for empty box

# H/V line rejection
CLEAN_LEN = 47  # window length (must be odd)
CLEAN_W   = 3   # line width-1 (even)
CLEAN_THR = 0.9 # rejection threshold

# Enum for checkbox state
class Checkbox_State(Enum):
    Unknown = -1
    Empty = 0
    Checked = 1
    Filled = 2

def load_image(path):
    image = Image.open(path)
    image = image.convert('L')
    image = ImageOps.autocontrast(image)
    return np.array(image)

def _svg_translate(tag, tx=0, ty=0):
    if tag is None:
        return tx, ty
    trn = tag.get('transform')
    if trn is not None:
        grp = re.match(r'^translate\(([-\d.]+),([-\d.]+)\)$', trn)
        if grp is None:
            logging.error('SVG node contains unsupported transformations!')
            sys.exit(1)
        tx += float(grp.group(1))
        ty += float(grp.group(2))
    return _svg_translate(tag.getparent(), tx, ty)

def load_svg_rects(path, shape):
    data = lxml.etree.parse(path).getroot()
    dw = shape[1] / float(data.get('width'))
    dh = shape[0] / float(data.get('height'))
    rects = []
    for tag in data.iterfind('.//{*}rect'):
        tx, ty = _svg_translate(tag)
        i = tag.get('id')
        x = int((float(tag.get('x')) + tx) * dw)
        y = int((float(tag.get('y')) + ty) * dh)
        w = int(float(tag.get('width')) * dw)
        h = int(float(tag.get('height')) * dh)
        rects.append((i, x, y, w, h))
    return rects


def clean_image(image):
    T = threshold_local(image, 11, offset=10, method="gaussian")
    clean = (image > T).astype("uint8")*255
    return clean


def scan_marks(image, marks):
    res = []
    for i, x, y, w, h in marks:
        # roi = image[y:y+h, x:x+w]
        # scr = (roi < BLACK_LEVEL).sum() / (w*h)
        roi = image[y:y+h, x:x+w] < BLACK_LEVEL
        masked = roi[1:-1,1:-1] & roi[:-2,1:-1] & roi[2:,1:-1] & roi[1:-1,:-2] & roi[1:-1,2:]
        scr = (masked).sum() / (w*h)
        if scr > FILL_THR:
            v = Checkbox_State.Filled
        elif scr > CHECK_THR:
            v = Checkbox_State.Checked
        elif scr < EMPTY_THR:
            v = Checkbox_State.Empty
        else:
            v = Checkbox_State.Unknown
        res.append((i, v, scr))
    return res


def debug_marks(path, image, clean, marks, res):
    buf = Image.new('RGB', image.shape[::-1])
    buf.paste(Image.fromarray(image, 'L'))
    draw = ImageDraw.Draw(buf, 'RGBA')
    for mark, row in zip(marks, res):
        i, x, y, w, h = mark
        v = row[1]
        if v == Checkbox_State.Checked:
            c = (0, 255, 0, 127) # green
        elif v == Checkbox_State.Empty:
            c = (255, 0, 0, 127) # red
        elif v == Checkbox_State.Filled:
            c = (0, 0, 0, 64) # gray
        else:
            c = (255, 127, 0, 127) # orange
        draw.rectangle((x, y, x+w, y+h), c)
    bw = clean.copy()
    thr = bw < BLACK_LEVEL
    bw[thr] = 255
    bw[~thr] = 0
    buf.paste((0, 127, 255),
              (0, 0, image.shape[1], image.shape[0]),
              Image.fromarray(bw, 'L'))
    buf.save(path)

def print_mark_output(res, path):
    headers = [("Checkbox ID", "OMR Outcome", "Score"), ("-----------", "-----------", "-----")]
    output = [(i, Checkbox_State(v).name, str(s)) for i, v, s in res]
    lines = headers + output
    col_width = max(len(word) for line in lines for word in line)
    with open(path,'w') as f:
        for line in lines:
            formatted_line = "\t".join(word.ljust(col_width) for word in line)
            f.write(formatted_line + "\n")
            print(formatted_line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('template', help='Data template (svg)')
    ap.add_argument('image', help='Image to analyze')
    ap.add_argument('text', help='Text output to file')
    ap.add_argument('-d', dest='debug', help='Debug marks to file')
    args = ap.parse_args()

    # load data
    image = load_image(args.image)
    marks = load_svg_rects(args.template, image.shape)
    if len(marks) == 0:
        logging.warn('template contains no marks')
        return 1

    # process
    clean = clean_image(image)
    res = scan_marks(clean, marks)
    if args.debug:
        debug_marks(args.debug, image, clean, marks, res)

    # output
    print_mark_output(res, args.text)

if __name__ == '__main__':
    sys.exit(main())
