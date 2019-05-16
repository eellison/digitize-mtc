# Contains pipeline for processing incoming form
import json
import cv2
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw
import csv
from scripts import *
from .align import *
from .omr import *
from .json_encoder import *
from .form_model import *
from .util import *


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
    template_image = util.read_image(template.form_image) # numpy.ndarray

    ###################################
    ### Step 1: Run Image Alignment ###
    ###################################
    aligned_image, aligned_diag_image, h = align.align_images(input_image, template_image)

    ####################################
    ### Step 2: Run Mark Recognition ###
    ####################################
    answered_questions, clean_input = omr.recognize_answers(aligned_image, template_image, template)

    ############################
    ### Step 3: Write Output ###
    ############################
    processed_form = Form(template.name, template.form_image, answered_questions)
    input_image_name, output_abs_path, json_output_path, csv_output_path = util.generate_paths(input_image_path, template, output_dir_path)
    # Write (1) diagnostic images, (2) JSON form representation, (3) CSV output
    util.write_diag_images(input_image_name, output_abs_path, aligned_image, aligned_diag_image, clean_input, answered_questions)
    util.write_form_to_json(processed_form, json_output_path)
    util.write_form_to_csv(processed_form, csv_output_path)

    return True # Side-effecting function
