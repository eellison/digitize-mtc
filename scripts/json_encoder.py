import json
from copy import deepcopy
from form_model import *

# JSON encoder for FormTemplate objects
class FormTemplateEncoder(JSON.JSONEncoder):
    def get_basic_dict(self, obj):
        dict_repr = deepcopy(obj.__dict__) # deepcopy to avoid Python's mutation by reference
        dict_repr["__type__"] = obj.__class__.__name__
        return dict_repr

    def default(self, obj):
        if isinstance(obj, FormTemplate):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["questions"] = [self.default(q) for q in obj.questions]
            return dict_repr
        elif isinstance(obj, Question):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["responses"] = [self.default(r) for r in obj.responses]
            return dict_repr
        elif isinstance(obj, Response):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["location"] = self.default(obj.location)
            return dict_repr
        elif isinstance(obj, Location):
            return self.get_basic_dict(obj)
        elif isinstance(obj, QuestionType) or isinstance(obj, AnswerStatus):
            return obj.name
        else:
            # Let the base class default method raise the TypeError
            json.JSONEncoder.default(self, obj)

# Decoder that converts JSON back to FormTemplate object (should be inverse of above)
def decode_form(form_json):
    if '__type__' in form_json and form_json['__type__'] == FormTemplate.__name__:
        questions = [decode_form(question) for question in form_json["questions"]]
        return FormTemplate(form_json['name'], form_json['form_image'], questions)
    elif '__type__' in form_json and form_json['__type__'] == Question.__name__:
        responses = [decode_form(response) for response in form_json["responses"]]
        return Question(form_json['name'], form_json['question_type'], responses)
    elif '__type__' in form_json and form_json['__type__'] == Response.__name__:
        location = decode_form(form_json['location'])
        return Response(form_json['name'], location)
    elif '__type__' in form_json and form_json['__type__'] == Location.__name__:
        return Location(form_json['x'], form_json['y'], form_json['width'], form_json['height'])
    else:
        raise Exception("Unable to convert JSON to internal FormTemplate model; No recognized __type__ field; %s" % json)



# Some simple tests for JSON Serialization / Deserialization
loc1 = Location(1, 2, 3, 4)
loc2 = Location(2, 4, 6, 8)
r1 = Response("R1", loc1)
r2 = Response("R2", loc2)
q1 = Question("Q1", "Radio Button", [r1])
q2 = Question("Q2", "Checkbox", [r2])
f = FormTemplate("anc template", "example/phone_pics/images", [q1, q2])

# print(decode(f.to_JSON()).to_JSON())
# with open('test.json', 'w') as json_file:
#     JSON.dump(f, json_file, cls=FormTemplateEncoder)

# with open('form.json', 'r') as json_file:
#     reconstructed_form = JSON.load(json_file)
    #print(reconstructed_form)



### JSON encoder / decoder ###
# Returns a dict that can be serialized to JSON
# def encode(py_class):
#     # Validate input
#     valid_encode_type = (FormTemplate, Question, Response, Location)
#     if type(py_class) not in valid_encode_type:
#         raise Exception("Unable to encode input %s: Expected a FormTemplate, Question, Response, or Location" % str(py_class))
#
#     dict = py_class.__dict__
#     dict["__type__"] = type(py_class).__name__
#     if isinstance(py_class, FormTemplate):
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

# class JSONable():
#     def __init__(self, json_tag):
#         self.json_tag = json_tag
#
#     def to_JSON(self):
#         dict_repr = self.__dict__
#         dict_repr["__type__"] = self.json_tag
#         for k, v in dict_repr.items():
#             if isinstance(v, JSONable):
#                 dict_repr[k] = v.to_JSON()
#             elif isinstance(v, list) and all(isinstance(n, JSONable) for n in v):
#                 dict_repr[k] = [n.to_JSON() for n in v]
#         return dict_repr
