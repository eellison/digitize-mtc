## Utility Functions for Form Processing

from pathlib import Path
from .json_encoder import *
from .form_model import *
import os
from PIL import Image, ImageDraw, ImageOps
import csv
import cv2

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
    ''' NOTE: The pathlib library is essential to ensure that that all
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
    with open(json_output_path, 'w') as json_file:
        json.dump(processed_form, json_file, cls=FormTemplateEncoder, indent=4)

def omr_visual_output(image, clean_image, answered_questions, output_path):
    # Currently only handles checkbox / radio button cases
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    buf = Image.new('RGB', image.shape[::-1])
    buf.paste(Image.fromarray(image, 'L'))
    draw = ImageDraw.Draw(buf, 'RGBA')
    for q in answered_questions:
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
    # Create paths
    aligned_diag_output_path = str(output_path / (input_image_name + "_aligned_diag.jpg"))
    aligned_output_path = str(output_path / (input_image_name + "_aligned.jpg"))
    debug_output_path = str(output_path / (input_image_name + "_omr_debug.png"))
    # Write images
    cv2.imwrite(aligned_diag_output_path, aligned_diag_image)
    cv2.imwrite(aligned_output_path, aligned_image)
    omr_visual_output(aligned_image, clean_input, answered_questions, debug_output_path)

# Shitty hardcoded fn to transform SVG coordinates to form (x, y) based on image size
# def transform_locations(template, shape):
#     dw = shape[1] / float(792)
#     dh = shape[0] / float(1121.28)
#     template_copy = deepcopy(template)
#     for question in template_copy.questions:
#         for response in question.responses:
#             loc = response.location
#             loc.x = int(float(loc.x) * dw)
#             loc.y = int(float(loc.y) * dh)
#             loc.w = int(float(loc.w) * dw)
#             loc.h = int(float(loc.h) * dh)
#     return template_copy
