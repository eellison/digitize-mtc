import json
from copy import deepcopy
from .form_model import *


# JSON encoder for FormTemplate objects
class FormTemplateEncoder(JSON.JSONEncoder):
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
             isinstance(obj, Checkbox_State):
            return obj.name
        else:
            # Let the base class default method raise the TypeError
            json.JSONEncoder.default(self, obj)

# Decoder that converts JSON back to FormTemplate object (should be inverse of above)
def decode_form(form_json):
    if '__type__' in form_json and form_json['__type__'] == Form.__name__:
        questions = [decode_form(question) for question in form_json["questions"]]
        return Form(form_json['name'], form_json['form_image'], questions)
    elif '__type__' in form_json and form_json['__type__'] == Question.__name__:
        responses = [decode_form(region) for region in form_json["response_regions"]]
        return Question(form_json['name'], form_json['question_type'], responses, form_json["answer"], form_json["answer_status"])
    elif '__type__' in form_json and form_json['__type__'] == ResponseRegion.__name__:
        return ResponseRegion(form_json['name'], form_json['w'], form_json['h'], form_json['x'], form_json['y'], form_json['value'])
    else:
        raise Exception("Unable to convert JSON to internal FormTemplate model; No recognized __type__ field; %s" % json)
