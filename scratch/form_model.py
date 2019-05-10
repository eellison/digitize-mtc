# Model for annotating forms
from collections import namedtuple
import json as JSON

class Form():
    def __init__(self, name, image, questions):
        self.name = name # name of data table
        self.image = image # path to image
        self.questions = questions # list of Question

    def to_JSON(self):
        dict_repr = self.__dict__
        dict_repr["__type__"] = Form.__name__
        dict_repr["questions"] = [q.to_JSON() for q in self.questions]
        return dict_repr

class Question():
    def __init__(self, name, type, responses):
        self.name = name # name of column in data table
        self.type = type # type of question, ex. checkbox, radio button
        self.responses = responses

    def to_JSON(self):
        dict_repr = self.__dict__
        dict_repr["__type__"] = Question.__name__
        dict_repr['responses'] = [r.to_JSON() for r in self.responses]
        return dict_repr

class Response():
    def __init__(self, name, location, background):
        self.name = name # meaning of the cell
        self.location =  location # Location; location within the template image
        self.background = background # array of background pixels within the template

    def to_JSON(self):
        dict_repr = self.__dict__
        dict_repr["__type__"] = Response.__name__
        dict_repr['location'] = self.location.to_JSON()
        return dict_repr

class Location():
    def __init__(self, x, y, width, height):
        self.x = x # x coordinate
        self.y = y # y coordinate
        self.width = width # width of bounding rectangle
        self.height = height # height of bounding rectangle

    def to_JSON(self):
        dict_repr = self.__dict__
        dict_repr["__type__"] = Location.__name__
        return dict_repr


### JSON encoder / decoder ###
# Returns a dict that can be serialized to JSON
# def encode(py_class):
#     # Validate input
#     valid_encode_type = (Form, Question, Response, Location)
#     if type(py_class) not in valid_encode_type:
#         raise Exception("Unable to encode input %s: Expected a Form, Question, Response, or Location" % str(py_class))
#
#     dict = py_class.__dict__
#     dict["__type__"] = type(py_class).__name__
#     if isinstance(py_class, Form):
#         encoded_questions = [encode(question) for question in py_class.questions]
#         dict["questions"] = encoded_questions
#         return dict
#     elif isinstance(py_class, Question):
#         encoded_responses = [encode(response) for response in py_class.responses]
#         dict["responses"] = encoded_responses
#         return dict
#     elif isinstance(py_class, Response):
#         encoded_location = encode(py_class.location)
#         dict["location"] = encoded_location
#         return dict
#     elif isinstance(py_class, Location):
#         return dict
#     else:
#         raise Exception("Invalid input class for JSON encoding.")

# Returns an object of type Form
def decode(json):
    if '__type__' in json and json['__type__'] == Form.__name__:
        questions = [decode(question) for question in json["questions"]]
        return Form(json['name'], json['image'], questions)
    elif '__type__' in json and json['__type__'] == Question.__name__:
        responses = [decode(response) for response in json["responses"]]
        return Question(json['name'], json['type'], responses)
    elif '__type__' in json and json['__type__'] == Response.__name__:
        location = decode(json['location'])
        return Response(json['name'], location, json['background'])
    elif '__type__' in json and json['__type__'] == Location.__name__:
        return Location(json['x'], json['y'], json['width'], json['height'])
    else:
        raise Exception("Unable to convert JSON to internal Form model; No recognized __type__ field; %s" % json)


def from_dict(d):
    return namedtuple("Form", d.keys())(*d.values())

loc1 = Location(1, 2, 3, 4)
loc2 = Location(2, 4, 6, 8)
r1 = Response("R1", loc1, [])
r2 = Response("R2", loc2, [])
q1 = Question("Q1", "Radio Button", [r1])
q2 = Question("Q2", "Checkbox", [r2])
f = Form("anc template", "example/phone_pics/images", [q1, q2])

print(decode(f.to_JSON()).to_JSON())
