'''
A Python script that generates a template for the ANC record
from a hardcoded model.

Eventually we will have a front-end interface that will allow users
to generate this template by uploading a form image and annotating it
themselves using a GUI.
'''
from form import *
import json
from pathlib import Path
import lxml.etree
from copy import deepcopy


class FormTemplateEncoder(json.JSONEncoder):
    def get_basic_dict(self, obj):
        dict_repr = deepcopy(obj.__dict__) # deepcopy to avoid Python's mutation by reference
        dict_repr["__type__"] = obj.__class__.__name__
        return dict_repr

    def default(self, obj):
        if isinstance(obj, Form):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["questions"] = [self.default(q) for q in obj.questions]
            return dict_repr
        elif isinstance(obj, Question):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["response_regions"] = [self.default(r) for r in obj.response_regions]
            return dict_repr
        elif isinstance(obj, ResponseRegion):
            dict_repr = self.get_basic_dict(obj)
            return dict_repr
        elif isinstance(obj, QuestionType) or \
             isinstance(obj, AnswerStatus) or \
             isinstance(obj, CheckboxState):
            return obj.name
        else:
            # Let the base class default method raise the TypeError
            json.JSONEncoder.default(self, obj)


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
abs_path_to_svg = str((Path.cwd() / "backend" / "forms" / "template_images" / "delivery_template_pg_1.svg").resolve())
abs_path_to_template_image = str((Path.cwd() / "backend" / "forms" / "template_images_v2" / "delivery_template_pg_1.jpg").resolve())

# Generate questions from SVG
all_questions = questions_from_svg(abs_path_to_svg)

# Create FormTemplate object
f = Form("ANC", abs_path_to_template_image, all_questions)

# Convert FormTemplate to JSON and write to file
with open('anc.json', 'w') as json_file:
    json.dump(f, json_file, cls=FormTemplateEncoder, indent=4)
