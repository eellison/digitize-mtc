import json
from copy import deepcopy
from .form_model import *
from .omr import Checkbox_State # remove this dependency by moving Checkbox_State into the FormModel



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
        elif isinstance(obj, ProcessedForm):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["answers"] = [self.default(a) for a in obj.answers]
            return dict_repr
        elif isinstance(obj, Answer):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["processed_responses"] = [self.default(pr) for pr in obj.processed_responses]
            return dict_repr
        elif isinstance(obj, ProcessedResponse):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["response"] = self.default(obj.response)
            return dict_repr
        elif isinstance(obj, QuestionType) or isinstance(obj, AnswerStatus) or isinstance(obj, Checkbox_State):
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
        return Location(form_json['x'], form_json['y'], form_json['w'], form_json['h'])
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
