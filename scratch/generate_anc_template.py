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
        resp = ResponseRegion("Checkbox[%s]" % question_name, w, h, x, y, None)
        q = Question(question_name, QuestionType.Checkbox, [resp], None, AnswerStatus.NotAnswered)
        questions.append(q)
    return questions

# Create Paths
abs_path_to_svg = str((Path.cwd() / "example" / "checkbox_locations.svg").resolve())
abs_path_to_template_image = str((Path.cwd() / "example" / "template.jpg").resolve())

# Generate questions from SVG
all_questions = questions_from_svg(abs_path_to_svg)

# Create FormTemplate object
f = Form("ANC", abs_path_to_template_image, all_questions)

# Convert FormTemplate to JSON and write to file
with open('anc.json', 'w') as json_file:
    json.dump(f, json_file, cls=FormTemplateEncoder, indent=4)
