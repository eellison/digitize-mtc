from enum import Enum

###########################
### Form Template Model ###
###########################

# TODO: rename FormContainer to Form and Form to Page
class FormContainer():
    def __init__(self, forms):
        self.forms = forms
        # TODO separate name
        self.name = forms[0].name


class Form():
    def __init__(self, name, image, width, height, question_groups):
        self.name = name # name of data table
        self.image = image # path to image of form
        self.w = width
        self.h = height
        self.question_groups = question_groups # list of QuestionGroup

class QuestionGroup():
    def __init__(self, name="Default", x=0, y=0, width=0, height=0, questions=None):
        questions = questions if questions is not None else []
        self.name = name
        self.w = width
        self.h = height
        self.x = x
        self.y = y
        self.questions = questions # list of Question

class Question():
    def __init__(self, name, question_type, response_regions, answer_status, expected_number_digits):
        self.name = name # name of column in data table
        self.question_type = question_type # QuestionType
        self.response_regions = response_regions # list of ResponseRegion
        self.answer_status = answer_status # AnswerStatus
        self.expected_number_digits = expected_number_digits

class ResponseRegion():
    def __init__(self, name, width, height, x, y, value):
        self.name = name # meaning of region
        self.w = width # width of bounding rectangle
        self.h = height # height of bounding rectangle
        self.x = x # x coordinate
        self.y = y # y coordinate
        self.value = value # the value of the region after processing (ex. checked/unchecked, some text)


#############
### Enums ###
#############
class QuestionType(Enum):
    # These names correspond to HTML form input types
    checkbox = 1
    radio = 2
    text = 3
    digits = 4

class AnswerStatus(Enum):
    unresolved = -1
    resolved = 1
    editted = 2

# Enum for checkbox state
class CheckboxState(Enum):
    unknown = -1
    empty = 0
    checked = 1
