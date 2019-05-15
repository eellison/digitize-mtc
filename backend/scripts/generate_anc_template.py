'''
A Python script that generates a template for the ANC record
from a hardcoded model.

Eventually we will have a front-end interface that will allow users
to generate this template by uploading a form image and annotating it
themselves using a GUI.
'''
from form_model import *
from json_encoder import FormTemplateEncoder
import json
from pathlib import Path
import lxml.etree

# Function to generate Questions from SVG
# For now, all questions are of type "Checkbox"
def questions_from_svg(svg_path):
    data = lxml.etree.parse(svg_path).getroot()
    dw = 2475 / float(data.get('width')) #hardcoded based on ANC image (example/template.jpg)
    dh = 3504 / float(data.get('height')) #hardcoded based on ANC image (example/template.jpg)
    questions = []
    for tag in data.iterfind('.//{*}rect'):
        question_name = tag.get('id')
        x = int(float(tag.get('x')) * dw)
        y = int(float(tag.get('y')) * dh)
        w = int(float(tag.get('width')) * dw)
        h = int(float(tag.get('height')) * dh)
        loc = Location(width=w, height=h, x=x, y=y)
        resp = Response("Checkbox[%s]" % question_name, loc)
        q = Question(question_name, QuestionType.Checkbox, [resp])
        questions.append(q)
    return questions

# Create Paths
abs_path_to_svg = str((Path.cwd() / "example" / "checkbox_locations.svg").resolve())
abs_path_to_template_image = str((Path.cwd() / "example" / "template.jpg").resolve())

# Generate questions from SVG
all_questions = questions_from_svg(abs_path_to_svg)

# Create FormTemplate object
f = FormTemplate("ANC_Template", abs_path_to_template_image, all_questions)

# Convert FormTemplate to JSON and write to file
with open('anc.json', 'w') as json_file:
    json.dump(f, json_file, cls=FormTemplateEncoder, indent=4)



### Below ###
### Hardcoded examples below to get a sense of how the forms are modeled ###

# Question 1: Is the patient less than 20 years of age?
loc_less_than_20 = Location(width=10.918688, height=11.758587, x=289.55521, y=359.28162)
resp_less_than_20 = Response("Checkbox[less_than_20]", loc_less_than_20)
less_than_20 = Question("less_than_20", QuestionType.Checkbox, [resp_less_than_20])

# Question 2: Has the patient had more than 4 prior deliveries?
loc_prior_deliveries = Location(width=11.548612, height=12.388511, x=337.8494, y=390.77783)
resp_prior_deliveries = Response("Checkbox[prior_deliveries]", loc_prior_deliveries)
prior_deliveries = Question("prior_deliveries", QuestionType.Checkbox, [resp_prior_deliveries])

# Question 3: Has the patient had a caesarean section in the past?
loc_c_section = Location(width=12.388511, height=12.80846, x=308.24295, y=469.72833)
resp_c_section = Response("Checkbox[c_section]", loc_c_section)
c_section = Question("c_section", QuestionType.Checkbox, [resp_c_section])
