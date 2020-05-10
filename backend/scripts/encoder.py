import json
from copy import deepcopy
from .form import *


# JSON encoder for Form objects
class FormTemplateEncoder(json.JSONEncoder):
    def get_basic_dict(self, obj):
        dict_repr = deepcopy(obj.__dict__) # deepcopy to avoid Python's mutation by reference
        dict_repr["__type__"] = obj.__class__.__name__
        return dict_repr

    def default(self, obj):
        if isinstance(obj, Form):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["question_groups"] = [self.default(q) for q in obj.question_groups]
            return dict_repr
        elif isinstance(obj, QuestionGroup):
            dict_repr = self.get_basic_dict(obj)
            dict_repr["questions"] = [self.default(q) for q in obj.questions]
            return dict_repr
        elif isinstance(obj, Question):
            dict_repr = self.get_basic_dict(obj)
            obj.response_regions = sorted(obj.response_regions, key=lambda rr: rr.name)
            dict_repr["response_regions"] = [self.default(r) for r in obj.response_regions]
            if isinstance(dict_repr["answer_status"], AnswerStatus):
                dict_repr["answer_status"] = self.default(obj.answer_status)
            # TODO add expected_number_digits
            return dict_repr
        elif isinstance(obj, ResponseRegion):
            dict_repr = self.get_basic_dict(obj)
            if isinstance(dict_repr["value"], CheckboxState):
                dict_repr["value"] = self.default(obj.value)
            return dict_repr
        elif isinstance(obj, QuestionType) or \
             isinstance(obj, AnswerStatus) or \
             isinstance(obj, CheckboxState):
            return obj.name
        else:
            # Let the base class default method raise the TypeError
            json.JSONEncoder.default(self, obj)

# Decoder that converts JSON back to FormTemplate object (should be inverse of above)
def decode_form(form_json):
    if isinstance(form_json, list):
        li = []
        for elem in form_json:
            decoded_elem = decode_form(elem)
            assert isinstance(decoded_elem, Form)
            li.append(decoded_elem)
        return FormContainer(li)
    if '__type__' in form_json and form_json['__type__'] == Form.__name__:
        question_groups = [decode_form(question) for question in form_json["question_groups"]]
        return Form(form_json['name'], form_json['image'], form_json['w'], form_json['h'], question_groups)
    if '__type__' in form_json and form_json['__type__'] == QuestionGroup.__name__:
        questions = [decode_form(question) for question in form_json["questions"]]
        return QuestionGroup(form_json['name'], form_json["w"],  form_json["h"],  form_json["x"],  form_json["y"], questions)
    elif '__type__' in form_json and form_json['__type__'] == Question.__name__:
        response_regions = [decode_form(region) for region in form_json["response_regions"]]
        expected_number_digits = None if not "expected_number_digits" in form_json else form_json["expected_number_digits"]
        return Question(form_json['name'], form_json['question_type'], response_regions, form_json["answer_status"], expected_number_digits)
    elif '__type__' in form_json and form_json['__type__'] == ResponseRegion.__name__:
        return ResponseRegion(form_json['name'], form_json['w'], form_json['h'], form_json['x'], form_json['y'], form_json['value'])
    else:
        raise Exception("Unable to convert JSON to internal FormTemplate model; No recognized __type__ field; %s" % form_json)
