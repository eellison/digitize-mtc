# Contains pipeline for processing incoming form
import json
import cv2
import sys
import align
import simpleomr as omr
from pathlib import Path
import os
from copy import deepcopy
from numpy import ndarray
from PIL import Image, ImageDraw
from form_model import *
import json_encoder

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
def generate_paths(path_to_input_image, output_dir_name):
    ''' NOTE: The pathlib library is essential to ensure that that all
    paths are operating-system agnostic. '''
    input_image_name = Path(path_to_input_image).stem # name of the input image file, minus the file extension
    try:
        os.makedirs(output_dir_name) # Make the directory if it doesn't exist
    except FileExistsError:
        pass # Skip Directory already exists
    output_path = Path.cwd() / output_dir_name # pathlib Path
    return input_image_name, output_path

def json_to_form_template(path_to_json_file):
    # Decode JSON template into
    with open(path_to_json_file, 'r') as json_template:
        loaded_json = json.load(json_template)
        template = json_encoder.decode_form(loaded_json)
    return template # of type FormTemplate


def get_checkbox_score(image, loc):
    roi = image[loc.y : loc.y + loc.h, loc.x : loc.x + loc.w] < BLACK_LEVEL
    masked = roi[1:-1,1:-1] & roi[:-2,1:-1] & roi[2:,1:-1] & roi[1:-1,:-2] & roi[1:-1,2:]
    scr = (masked).sum() / (loc.w * loc.h)
    return scr

def get_checkbox_state(input_image, template_image, checkbox_location):
    input_score = get_checkbox_score(input_image, checkbox_location)
    template_score = get_checkbox_score(template_image, checkbox_location)
    # Subtact the two scores, ie. how much more filled is the input than the template?
    scr = input_score - template_score
    if scr > FILL_THR:
        return omr.Checkbox_State.Filled
    elif scr > CHECK_THR:
        return omr.Checkbox_State.Checked
    elif scr < EMPTY_THR:
        return omr.Checkbox_State.Empty
    else:
        return omr.Checkbox_State.Unknown

def get_checkbox_answer(question, input_image, template_image):
    state = get_checkbox_state(input_image, template_image, question.responses[0].location)
    answer_status = AnswerStatus.NeedsRevision if state == omr.Checkbox_State.Unknown else AnswerStatus.Resolved
    answer_value = True if state == omr.Checkbox_State.Checked else False
    processed_response = ProcessedResponse(question.responses[0], state)
    return Answer(question.name, answer_status, answer_value, [processed_response], None)

def get_answer(question, input_image, template_image):
    # Based on question type
    print(question.question_type)
    print(QuestionType.Checkbox)
    if question.question_type == QuestionType.Checkbox.name:
        return get_checkbox_answer(question, input_image, template_image)
    else:
        # No logic for other question types, yet...
        print("Warning: could not process question type %s, skipping for now, " % str(question.question_type))
        return Answer(question.name, AnswerStatus.NeedsRevision, None, [], None)

def process_image(image_path, template):
    # Load and clean images
    input_image = omr.load_image(image_path)
    template_image = omr.load_image(str(Path.cwd() / template.form_image))
    clean_input = omr.clean_image(input_image)
    clean_template = omr.clean_image(template_image)
    template = transform_locations(template, input_image.shape)
    # Get answers
    answers = [get_answer(question, clean_input, clean_template) for question in template.questions]
    # Return output
    return input_image, clean_input, answers

def create_omr_debug(image, clean_image, answers, output_path):
    # Currently only handles checkbox / radio button cases
    buf = Image.new('RGB', image.shape[::-1])
    buf.paste(Image.fromarray(image, 'L'))
    draw = ImageDraw.Draw(buf, 'RGBA')
    for answer in answers:
        for processed_response in answer.processed_responses:
            loc = processed_response.response.location
            val = processed_response.value
            if val == omr.Checkbox_State.Checked:
                c = (0, 255, 0, 127) # green
            elif val == omr.Checkbox_State.Empty:
                c = (255, 0, 0, 127) # red
            elif val == omr.Checkbox_State.Filled:
                c = (0, 0, 0, 64) # gray
            else:
                c = (255, 127, 0, 127) # orange
            draw.rectangle((loc.x, loc.y, loc.x+loc.w, loc.y+loc.h), c)
    bw = clean_image.copy()
    thr = bw < BLACK_LEVEL
    bw[thr] = 255
    bw[~thr] = 0
    buf.paste((0, 127, 255),
              (0, 0, image.shape[1], image.shape[0]),
              Image.fromarray(bw, 'L'))
    buf.save(output_path)

def transform_locations(template, shape):
    # Shitty hardcoded fn while we figure out how to replace SVG entirely
    dw = shape[1] / float(792)
    dh = shape[0] / float(1121.28)
    template_copy = deepcopy(template)
    for question in template_copy.questions:
        for response in question.responses:
            loc = response.location
            loc.x = int(float(loc.x) * dw)
            loc.y = int(float(loc.y) * dh)
            loc.w = int(float(loc.w) * dw)
            loc.h = int(float(loc.h) * dh)
    return template_copy

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
    input_image_name, output_path = generate_paths(input_image_path, output_dir_path)
    input_image_path = str(Path(input_image_path).resolve())  # absolute path
    matched_output_path = str(output_path / (input_image_name + "_matched.jpg"))
    aligned_output_path = str(output_path / (input_image_name + "_aligned.jpg"))
    text_output_path = str(output_path / (input_image_name + "_omr_classification.txt"))
    debug_output_path = str(output_path / (input_image_name + "_omr_debug.png"))
    processed_form_json_path = str(output_path / (input_image_name + "_processed.json"))
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
    input_image, clean_input, answers = process_image(aligned_output_path, template)
    print([answer.value for answer in answers])
    create_omr_debug(input_image, clean_input, answers, debug_output_path)

    ############################################################
    ### Step 3: Contruct ProcessedForm and Serialize to JSON ###
    ############################################################
    processed_form = ProcessedForm(template, input_image_path, matched_output_path, aligned_output_path, debug_output_path, answers)
    # Convert template to JSON and write to file
    with open(processed_form_json_path, 'w') as json_file:
        json.dump(processed_form, json_file, cls=json_encoder.FormTemplateEncoder, indent=4)

    return True # Side-effecting function


input_pic = "example/phone_pics/input/sample_pic.jpg"
json_template = "scripts/anc.json"
print(process(input_pic, json_template, "big_boi_output"))
