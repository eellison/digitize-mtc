## Utility Functions for Form Processing
from pathlib import Path
from .encoder import *
from .form import *
import os
from PIL import Image, ImageDraw, ImageOps
import csv
import cv2
from copy import deepcopy
import numpy as np
import math
from skimage.filters import threshold_local

# CONSTANTS
BLACK_LEVEL  = 0.5 * 255

def read_image(image_path):
    """
    Args:
        image_path (str): path to image
    Returns:
        loaded_image (numpy.ndarray): Color representation of image
    """
    loaded_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    return loaded_image

def generate_paths(path_to_input_image, template, output_dir_name):
    '''
    Args:
        path_to_input_image (str)
        template (Form)
        output_dir_name (str)
    Returns:
        input_image_name (str): name of input image, without file extension
        output_abs_path (str): absolute path to output directory
        json_path (str): path to write JSON output
        csv_path (str): path to CSV file to append results to
    NOTE: The pathlib library is essential to ensure that that all
    paths are operating-system agnostic. '''
    input_image_name = Path(path_to_input_image).stem # name of the input image file, minus the file extension
    try:
        os.makedirs(output_dir_name) # Make the directory if it doesn't exist
    except FileExistsError:
        pass # Skip Directory already exists
    output_abs_path = Path.cwd() / output_dir_name # pathlib Path
    json_path = str(output_abs_path / (input_image_name + "_processed.json"))
    csv_path = str(output_abs_path / (template.name + ".csv"))
    return input_image_name, output_abs_path, json_path, csv_path

def read_json_to_form(path_to_json_file):
    """
    Args:
        path_to_json_file (str): file with JSON for file
    Returns:
        template (Form): a template for the form (with no answers filled in)
    """
    with open(path_to_json_file, 'r') as json_template:
        loaded_json = json.load(json_template)
        template = decode_form(loaded_json)
    return template

def write_form_to_json(processed_form, json_output_path):
    """
    Args:
        processed_form (Form): form with answers filled in
        json_output_path (str): path to dump JSON file
    """
    with open(json_output_path, 'w') as json_file:
        json.dump(processed_form, json_file, cls=FormTemplateEncoder, indent=4)

def omr_visual_output(image, clean_image, answered_questions, output_path):
    """
    Args:
        image (numpy.ndarray): input image, aligned to form template
        clean_image (numpy.ndarray): input image after cleaning step
        answered_questions (List[Question]): questions with answers filled in
        output_path (str): path to write omr visual output

    NOTE: Currently only handles checkbox / radio button cases
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    buf = Image.new('RGB', image.shape[::-1])
    buf.paste(Image.fromarray(image, 'L'))
    draw = ImageDraw.Draw(buf, 'RGBA')
    for group in answered_questions:
        for q in group.questions:
            for rr in q.response_regions:
                val = rr.value
                if val == CheckboxState.Checked:
                    c = (0, 255, 0, 127) # green
                elif val == CheckboxState.Empty:
                    c = (255, 0, 0, 127) # red
                elif val == CheckboxState.Filled:
                    c = (0, 0, 0, 64) # gray
                else:
                    c = (255, 127, 0, 127) # orange
                draw.rectangle((rr.x, rr.y, rr.x+rr.w, rr.y+rr.h), c)
    bw = clean_image.copy()
    thr = bw < BLACK_LEVEL
    bw[thr] = 255
    bw[~thr] = 0
    buf.paste((0, 127, 255),
              (0, 0, image.shape[1], image.shape[0]),
              Image.fromarray(bw, 'L'))
    buf.save(output_path)

def write_form_to_csv(processed_form, path_to_csv):
    """
    Args:
        processed_form (Form): with answers filled in
        path_to_csv: location of CSV to append results to
    """
    # Get list of answer values, which will form a new row of the CSV
    answer_values = [[question.answer for question in processed_form.questions]]
    # Check if the file already exists
    file_existed_already = os.path.isfile(path_to_csv)
    # Open file in "append" mode
    with open(path_to_csv,"a+") as csv_file:
        writer = csv.writer(csv_file)
        # Write header if file did not already exist
        if not file_existed_already:
            header_line = [[question.name for question in processed_form.questions]]
            writer.writerows(header_line)
        # Now append answers from the ProcessedForm
        writer.writerows(answer_values)
    return True

def write_diag_images(input_image_name, output_path, aligned_image, aligned_diag_image, clean_input, answered_questions):
    """
    Args:
        input_image_name (str): name of input image
        output_path (str): absolute path to the output directory
        aligned_image (numpy.ndarray): input image after alignment to template form
        aligned_diag_image (numpy.ndarray): visual diagnostic of alignment algo
        clean_input (numpy.ndarray): input image after cleaning step
        answered_questions (List[Question]): questions with answers filled in
    """
    # Create paths
    aligned_filename = input_image_name + "_aligned.jpg"
    aligned_diag_output_path = str(output_path / (input_image_name + "_aligned_diag.jpg"))
    aligned_output_path = str(output_path / aligned_filename)
    static_path = str(Path.cwd() / "backend" / "static" / aligned_filename)
    debug_output_path = str(output_path / (input_image_name + "_omr_debug.png"))
    # Write images
    cv2.imwrite(aligned_diag_output_path, aligned_diag_image)
    cv2.imwrite(aligned_output_path, aligned_image)
    cv2.imwrite(static_path, aligned_image) # also write to static/ for frontend access
    omr_visual_output(aligned_image, clean_input, answered_questions, debug_output_path)
    return aligned_filename # name of the file that can be found in static/ for frontend access


def remove_checkbox_outline(input_arr, region_name, debug=False):
    '''
    Args:
        arr (numpy.ndarray): a grayscale array containing a checkbox outline
    Returns:
        fin (numpy.ndarray): arr, with any vertical or horizontal lines removed
    '''
    arr = deepcopy(input_arr)
    thresh = cv2.adaptiveThreshold(
                        arr, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                        cv2.THRESH_BINARY_INV, 25, 15)
    # Create the images that will use to extract the horizontal and vertical lines
    horizontal = np.copy(thresh)
    vertical = np.copy(thresh)

    # Specify size on horizontal axis
    cols = horizontal.shape[1]
    horizontal_size = math.ceil(cols / 4) # specify a "line" as 1/4 length of image

    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))

    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    # Specify size on vertical axis
    rows = vertical.shape[0]
    verticalsize = math.ceil(rows / 4) # specify a "line" as 1/4 length of image

    # Create structure element for extracting vertical lines through morphology operations
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))

    # Apply morphology operations
    vertical = cv2.erode(vertical, verticalStructure)
    vertical = cv2.dilate(vertical, verticalStructure)

    # Add horizontal and vertical
    horizontal_plus_vertical = horizontal + vertical

    # Create final image after removal of boundary box
    boundary_box_idx = horizontal_plus_vertical!=0
    fin = deepcopy(input_arr)
    fin[boundary_box_idx] = horizontal_plus_vertical[boundary_box_idx]

    # Show extracted lines
    if debug:
        cv2.imwrite(region_name + "_original.jpg", input_arr)
        cv2.imwrite(region_name + "_horizontal.jpg", horizontal)
        cv2.imwrite(region_name + "_vertical.jpg", vertical)
        cv2.imwrite(region_name + "_horizontal_plus_vertical.jpg", horizontal_plus_vertical)
        cv2.imwrite(region_name + "checkbox_removed.jpg", fin)

    return fin

def project_mark_locations(image, form):
    """
    Args:
        image (numpy.ndarray): input image for mark recognition
        form (Form): template for a form, with coordinates in absolute terms
    Returns:
        form (Form): same input form, but with coordinates translated relative to input image size
    """
    # TODO: Clean this up; Sud: I think the form model needs a nested "Location"
    image_height, image_width = image.shape
    dw = image_width / form.w
    dh = image_height / form.h
    # re-assign dimensions to input image dimensions
    form.w = image_width
    form.h = image_height
    # project all marks onto new coordinate system
    for group in form.question_groups:
        group.w = int(float(group.w) * dw)
        group.h = int(float(group.h) * dh)
        group.x = int(float(group.x) * dw)
        group.y = int(float(group.y) * dh)
        for question in group.questions:
            for region in question.response_regions:
                region.w = int(float(region.w) * dw)
                region.h = int(float(region.h) * dh)
                region.x = int(float(region.x) * dw)
                region.y = int(float(region.y) * dh)
    return form

def clean_image(image):
    """
    Args:
        image (numpy.ndarray): image to clean
    Returns:
        clean (numpy.ndarray): cleaned image
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    T = threshold_local(image, 11, offset=10, method="gaussian")
    clean = (image > T).astype("uint8")*255
    return clean
