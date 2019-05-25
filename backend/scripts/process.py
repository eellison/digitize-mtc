import cv2
import os
from pathlib import Path
from PIL import Image, ImageDraw
from . import *


def process(input_image_path, template_json_path, output_dir_path):
    '''
    Args:
        input_image_path (str): path to input image, ie. a filled form
        template_json_path (str): path to JSON file specifying modeled Form
        output_dir_path (str): path to write output
    '''

    #########################################################
    ### Step 0: Load input image + template, assign paths ###
    #########################################################
    # Load input image, template, and template_image
    input_image = util.read_image(input_image_path) # numpy.ndarray
    template = util.read_json_to_form(template_json_path) # Form object
    template_image = util.read_image(template.image) # numpy.ndarray

    ###################################
    ### Step 1: Run Image Alignment ###
    ###################################
    aligned_image, aligned_diag_image, h = align.align_images(input_image, template_image)

    ####################################
    ### Step 2: Run Mark Recognition ###
    ####################################
    answered_questions, clean_input = omr.recognize_answers(aligned_image, template_image, template)

    ###########################
    ### Step 3: Write Output ###
    ############################
    input_image_name, output_abs_path, json_output_path, csv_output_path = util.generate_paths(input_image_path, template, output_dir_path)
    # Write (1) diagnostic images, (2) JSON form representation
    aligned_filename = util.write_diag_images(input_image_name, output_abs_path, aligned_image, aligned_diag_image, clean_input, answered_questions)
    # Create and return processed form
    processed_form = Form(template.name, aligned_filename, template.w, template.h, answered_questions)
    util.write_form_to_json(processed_form, json_output_path)
    return processed_form
