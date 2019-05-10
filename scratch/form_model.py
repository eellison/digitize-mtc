# Model for annotating forms
from collections import namedtuple
import json as JSON

class Form():
    def __init__(self, name, image, questions):
        self.name = name # name of data table
        self.image = image # path to image
        self.questions = questions # list of Question

    def from_dict(d):
        return namedtuple("Form", d.keys())(*d.values())

class Question():
    def __init__(self, name, type, responses):
        self.name = name # name of column in data table
        self.type = type # type of question, ex. checkbox, radio button
        self.responses = responses

class Response():
    def __init__(self, name, location, background):
        self.name = name # meaning of the cell
        self.location =  location # Location; location within the template image
        self.background = background # array of background pixels within the template

class Location():
    def __init__(self, x, y, width, height):
        self.x = x # x coordinate
        self.y = y # y coordinate
        self.width = width # width of bounding rectangle
        self.height = height # height of bounding rectangle

### A JSON Decoder ###
def form_decoder(json):
    if '__type__' in json and json['__type__'] == 'Form':
        questions = [form_decoder(question) for question in json.questions]
        return Form(json['name'], json['image'], questions)
    elif '__type__' in json and json['__type__'] == 'Question':
        responses = [form_decoder(response) for response in json.responses]
        return Question(json['name'], json['type'], responses)
    elif '__type__' in json and json['__type__'] == 'Response':
        location = form_decoder(json['location'])
        return Response(json['name'], location, json['background'])
    elif '__type__' in json and json['__type__'] == 'Location':
        return Location(json['x'], json['y'], json['width'], json['height'])
    else:
        raise Exception("Invalid JSON: unable to convert to internal Form model")


q1 = Question("Q1", "Radio Button")
q2 = Question("Q2", "Checkbox")
f = Form("anc template", "example/phone_pics/images", ["Q1", "Q2"])

f_as_dict = f.__dict__
print(f.__dict__)
f_converted_back = Form.from_dict(f_as_dict)
print(f_converted_back)
print(f_converted_back.name)
