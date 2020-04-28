'''
A Python script that generates a JSON template for a form
based on an SVG with tagged rectangles

Eventually we will have a front-end interface that will allow users
to generate this template by uploading a form image and annotating it
themselves using a GUI.
'''
from form import *
import json
from pathlib import Path
import lxml.etree
from copy import deepcopy
from encoder import FormTemplateEncoder
import util


############
### NOTE ###
############
'''
The code below relies on having an SVG with all rectangles marked
in the following format

qg_[question group name]_[question type]_[response name]

...where
[question group name] is the name of one of the question groups
[question type] is the type of question (either "rb" for radio button, "cb" for checkbox, or "ocr" for text)
[response name] is the name of the response if the type is radio (ex. "yes" or "no")
'''

########################
### Helper Functions ###
########################
def get_pixel_dimensions(tag, dw, dh):
    w = float(tag.get('width'))
    h = float(tag.get('height'))
    x = float(tag.get('x'))
    y = float(tag.get('y'))
    return w, h, x ,y

def get_tag_parts(tag):
    tag_name = tag.get('id')
    split_name = tag_name.rsplit("_")
    group_name = split_name[1]
    question_type = split_name[2]
    question_name = split_name[3]
    if question_type == "rb" and len(split_name) == 5:
        response_name = split_name[4]
    else:
        response_name = None
    return group_name, question_type, question_name, response_name

# Function to generate Questions from SVG, and put them into question groups
def questions_from_svg(svg_path):
    data = lxml.etree.parse(svg_path).getroot()
    # TODO: get these from the image file itself
    template_width = float(data.get('width'))
    template_height = float(data.get('height'))
    # dw = 1275 / template_width #hardcoded based on ANC image (example/template.jpg)
    # dh = 1650 / template_height #hardcoded based on ANC image (example/template.jpg)

    # First find the question groups
    question_groups = {}
    for tag in data.iterfind('.//{*}rect'):
        tag_name = tag.get('id')
        if tag_name[:2] != 'qg' and tag_name[:2] != 'gq': # only QuestionGroups don't start with qg
            w, h, x, y = get_pixel_dimensions(tag, None, None)
            new_group = QuestionGroup(tag_name, w, h, x, y, [])
            question_groups[tag_name] = new_group

    # Now generate questions and place them in the right group
    rb_tag_list = []
    for tag in data.iterfind('.//{*}rect'):
        tag_name = tag.get('id')
        if tag_name[:2] == 'qg' or tag_name[:2] == 'gq':
            group_name, question_type, question_name, response_name = get_tag_parts(tag)
            w, h, x, y = get_pixel_dimensions(tag, None, None)
            if question_type == "rb":
                rb_tag_list.append(tag)
                continue
            else:
                new_response_region = ResponseRegion("", w, h, x, y, None)
                new_question = Question(question_name, None, [new_response_region], AnswerStatus.unresolved, 0)
                if question_type == "ocr":
                    new_question.question_type = QuestionType.text
                elif question_type == "cb":
                    new_question.question_type = QuestionType.checkbox
                else:
                    raise Exception("Unknown question type %s in SVG!!" % question_type)
                question_groups[group_name].questions.append(new_question)

    # Handle radio button questions separately
    radio_questions, question_to_group = create_radio_questions(rb_tag_list, None, None)
    for question in radio_questions:
        group = question_to_group[question.name]
        question_groups[group].questions.append(question)

    # Output the question groups as a list
    return(list(question_groups.values()), template_width, template_height)

def create_radio_questions(tag_list, dw, dh):
    # First, construct all of the radio questions
    all_question_names = set(get_tag_parts(t)[2] for t in tag_list)
    # Create and group responses
    response_dict = {name:[] for name in all_question_names} # map from question name to response regions
    question_to_group_dict = {}
    for tag in tag_list:
        tag_name = tag.get('id')
        group_name, question_type, question_name, response_name = get_tag_parts(tag)
        w, h, x, y = get_pixel_dimensions(tag, dw, dh)
        new_response = ResponseRegion(response_name, w, h, x, y, None)
        response_dict[question_name].append(new_response)
        question_to_group_dict[question_name] = group_name

    # Construct questions from grouped responses
    all_questions = []
    for question_name, response_regions in response_dict.items():
        new_question = Question(question_name, QuestionType.radio, response_regions, AnswerStatus.unresolved, 0)
        all_questions.append(new_question)

    return all_questions, question_to_group_dict


##########################
### Run the Conversion ###
##########################

# Create Paths / names
form_name = "COVID"
template_file_name = "covid_full.json"
abs_path_to_svg = str((Path.cwd() / "Case_Report_Form_Full.svg").resolve())
relative_path_to_template_image = str(Path("") / "backend" / "forms" / "template_images_v2" / "Case_Report_Form.jpeg")

# Generate questions from SVG
(all_question_groups, template_width, template_height) = questions_from_svg(abs_path_to_svg)
(template_height_cv2, template_width_cv2) = util.get_image_dimensions(relative_path_to_template_image)

print(template_width)
print(template_height)
print(template_width_cv2)
print(template_height_cv2)

# Create Form object
form = Form(form_name, relative_path_to_template_image, template_width, template_height, all_question_groups)

# Convert Form to JSON and write to file
with open(template_file_name, 'w') as json_file:
    json.dump(form, json_file, cls=FormTemplateEncoder, indent=4)
