# Model for annotating forms
from collections import namedtuple
import json as JSON

class Form():
    def __init__(self, name, image, questions):
        self.name = name # name of data table
        self.image = image # path to image
        self.questions = questions # list of Question

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

### JSON encoder / decoder ###
# Returns a dict that can be serialized to JSON
def encode(py_class):
    # Validate input
    valid_encode_type = (Form, Question, Response, Location)
    if type(py_class) not in valid_encode_type:
        raise Exception("Unable to encode input %s: Expected a Form, Question, Response, or Location" % str(py_class))

    dict = py_class.__dict__
    dict["__type__"] = type(py_class).__name__
    if isinstance(py_class, Form):
        encoded_questions = [encode(question) for question in py_class.questions]
        dict["questions"] = encoded_questions
        return dict
    elif isinstance(py_class, Question):
        encoded_responses = [encode(response) for response in py_class.responses]
        dict["responses"] = encoded_responses
        return dict
    elif isinstance(py_class, Response):
        encoded_location = encode(py_class.location)
        dict["location"] = encoded_location
        return dict
    elif isinstance(py_class, Location):
        return dict
    else:
        raise Exception("Invalid input class for JSON encoding.")

# Returns an object of type Form
def decode(json):
    if '__type__' in json and json['__type__'] == type(Form).__name__:
        questions = [decode(question) for question in json.questions]
        return Form(json['name'], json['image'], questions)
    elif '__type__' in json and json['__type__'] == type(Question).__name__:
        responses = [decode(response) for response in json.responses]
        return Question(json['name'], json['type'], responses)
    elif '__type__' in json and json['__type__'] == type(Response).__name__:
        location = decode(json['location'])
        return Response(json['name'], location, json['background'])
    elif '__type__' in json and json['__type__'] == type(Location).__name__:
        return Location(json['x'], json['y'], json['width'], json['height'])
    else:
        raise Exception("Unable to convert JSON to internal Form model; No recognized __type__ field")


def from_dict(d):
    return namedtuple("Form", d.keys())(*d.values())

loc1 = Location(1, 2, 3, 4)
loc2 = Location(2, 4, 6, 8)
r1 = Response("R1", loc1, [])
r2 = Response("R2", loc2, [])
q1 = Question("Q1", "Radio Button", [r1, r2])
q2 = Question("Q2", "Checkbox", [r1, r2])
f = Form("anc template", "example/phone_pics/images", [q1, q2])

print(Form.__name__)
print(f)
print(encode(f))
