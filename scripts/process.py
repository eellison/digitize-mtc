# Contains pipeline for processing incoming form
import json
from form_model import *
import json_encoder
import cv2
import align
import simpleomr

'''
Process Function

Input:
path_to_input_image  :  str
                        path to the uploaded input (ie. a picture of a filled form)
path_to_template     :  str
                        path to template, specified by JSON file
'''
def process(path_to_input_image, path_to_template):
    # Load input image
    input_image = cv2.imread(path_to_input_image, cv2.IMREAD_COLOR)

    # Decode JSON template into
    with open(path_to_template, 'r') as json_template:
        loaded_json = json.load(json_template)
        template = json_encoder.decode_form(loaded_json) # of type FormTemplate

'''get this pathing right!!'''
    # Load image template
    # print(template.form_image)
    # template_image = cv2.imread(template.form_image, cv2.IMREAD_COLOR)
    # im_registered, im_matches, h = align.alignImages(input_image, template_image)

    return 42

input_pic = "example/phone_pics/sample_pic.jpg"
json_template = "scripts/anc.json"
print(process(input_pic, json_template))
