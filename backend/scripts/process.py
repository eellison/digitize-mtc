# Contains pipeline for processing incoming form
import json
import cv2
import sys
import os
from copy import deepcopy
from numpy import ndarray
from pathlib import Path
from PIL import Image, ImageDraw
import csv
from scripts import *
from .align import *
from .omr import *
from .json_encoder import *
from .form_model import *


## # TODO:
# - Answers actually contain cutouts of the final debug image
# - Create script that deserializes a processed_form and writes results to a CSV
# - question types other than checkbox
# - clean up directory structure
# - sort out align and simpleomr as scripts or python packages or binaries
# - consolidate input loading / processing (only cv2 or only Image)
# - un-hardcode the size of the SVG
# - start using type_checker

# CONSTANTS
BLACK_LEVEL  = 0.5 * 255
FILL_THR     = 0.11 # threshold for filled box
CHECK_THR    = 0.04 # threshold for checked box
EMPTY_THR    = 0.02 # threashold for empty box

##################
### Helper Fns ###
##################
def generate_paths(path_to_input_image, path_to_template_image, output_dir_name):
    ''' NOTE: The pathlib library is essential to ensure that that all
    paths are operating-system agnostic. '''
    input_image_name = Path(path_to_input_image).stem # name of the input image file, minus the file extension
    template_name = Path(path_to_template_image).stem
    try:
        os.makedirs(output_dir_name) # Make the directory if it doesn't exist
    except FileExistsError:
        pass # Skip Directory already exists
    output_path = Path.cwd() / output_dir_name # pathlib Path
    return input_image_name, template_name, output_path

def json_to_form_template(path_to_json_file):
    # Decode JSON template into
    with open(path_to_json_file, 'r') as json_template:
        loaded_json = json.load(json_template)
        template = json_encoder.decode_form(loaded_json)
    return template # of type Form


def get_checkbox_score(image, loc):
    roi = image[loc.y : loc.y + loc.h, loc.x : loc.x + loc.w] < BLACK_LEVEL
    masked = roi[1:-1,1:-1] & roi[:-2,1:-1] & roi[2:,1:-1] & roi[1:-1,:-2] & roi[1:-1,2:]
    scr = (masked).sum() / (loc.w * loc.h)
    return scr

def get_checkbox_state(input_image, template_image, response_region):
    input_score = get_checkbox_score(input_image, response_region)
    template_score = get_checkbox_score(template_image, response_region)
    # Subtact the two scores, ie. how much more filled is the input than the template?
    scr = input_score #- template_score
    checkbox_state = None
    if scr > FILL_THR:
        checkbox_state = CheckboxState.Filled
    elif scr > CHECK_THR:
        checkbox_state =  CheckboxState.Checked
    elif scr < EMPTY_THR:
        checkbox_state =  CheckboxState.Empty
    else:
        checkbox_state =  CheckboxState.Unknown
    response_region.value = checkbox_state
    return checkbox_state

def get_checkbox_answer(question, input_image, template_image):
    state = get_checkbox_state(input_image, template_image, question.response_regions[0])
    answer_status = AnswerStatus.NeedsRevision if state == CheckboxState.Unknown else AnswerStatus.Resolved
    answer_value = True if state == CheckboxState.Checked else False
    question.answer_status = answer_status
    question.answer = answer_value
    return question

def get_answer(question, input_image, template_image):
    # Based on question type
    if question.question_type == QuestionType.Checkbox.name:
        return get_checkbox_answer(question, input_image, template_image)
    else:
        # No logic for other question types, yet...
        print("Warning: could not process question type %s, skipping for now, " % str(question.question_type))
        return question

def process_image(image_path, template):
    # Load and clean images
    input_image = omr.load_image(image_path)
    template_image = omr.load_image(str(Path.cwd() / template.form_image))
    clean_input = omr.clean_image(input_image)
    clean_template = omr.clean_image(template_image)
    #template = transform_locations(template, input_image.shape)
    # Get answers
    answered_questions = [get_answer(question, clean_input, clean_template) for question in template.questions]
    # Return output
    return input_image, clean_input, answered_questions

def create_omr_debug(image, clean_image, answered_questions, output_path):
    # Currently only handles checkbox / radio button cases
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

# def transform_locations(template, shape):
#     # Shitty hardcoded fn while we figure out how to replace SVG entirely
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


'''
@processed_form: ProcessedForm
@path_to_csv: str   Location of CSV file to write to
'''
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

'''
Process Function

Input:
- input_image_path (str): path to input image
- template_json_path (str): path to JSON file specifying the form template
- output_dir_path (str): path to write all output to

'''
def process(input_image_path, template_json_path, output_dir_path):

    #########################################################
    ### Step 0: Load input image + template, assign paths ###
    #########################################################
    # Generate paths / file names for later use
    input_image_name, template_name, output_path = generate_paths(input_image_path, template_json_path, output_dir_path)
    input_image_path = str(Path(input_image_path).resolve())  # absolute path
    matched_output_path = str(output_path / (input_image_name + "_matched.jpg"))
    aligned_output_path = str(output_path / (input_image_name + "_aligned.jpg"))
    text_output_path = str(output_path / (input_image_name + "_omr_classification.txt"))
    debug_output_path = str(output_path / (input_image_name + "_omr_debug.png"))
    processed_form_json_path = str(output_path / (input_image_name + "_processed.json"))
    processed_form_csv_path = str(output_path / (template_name + ".csv"))
    # Load input image
    input_image = align.read_image(input_image_path)
    # Load FormTemplate and the embedded template_image
    template = json_to_form_template(template_json_path) # FormTemplate
    template_image_path = str(Path.cwd() / template.form_image)
    template_image = align.read_image(template_image_path)


    ###################################
    ### Step 1: Run Image Alignment ###
    ###################################
    im_registered, im_matches, h = align.alignImages(input_image, template_image)
    # Write output to file
    cv2.imwrite(matched_output_path, im_matches)
    cv2.imwrite(aligned_output_path, im_registered)

    ####################################
    ### Step 2: Run Mark Recognition ###
    ####################################
    input_image, clean_input, answered_questions = process_image(aligned_output_path, template)
    create_omr_debug(input_image, clean_input, answered_questions, debug_output_path)

    ############################################################
    ### Step 3: Contruct ProcessedForm and Serialize to JSON ###
    ############################################################
    processed_form = Form(template.name, template.form_image, answered_questions)
    # Convert template to JSON and write to JSON file (in production, would send to front end)
    with open(processed_form_json_path, 'w') as json_file:
        json.dump(processed_form, json_file, cls=json_encoder.FormTemplateEncoder, indent=4)

    # Write template to CSV file
    write_form_to_csv(processed_form, processed_form_csv_path)

    return True # Side-effecting function


# input_pic = "example/phone_pics/input/sample_pic.jpg"
# json_template = "backend/scripts/anc.json"
# process(input_pic, json_template, "output")
