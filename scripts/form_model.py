# Model for annotating forms
import json as JSON
from enum import Enum
from copy import deepcopy





###########################
### Form Template Model ###
###########################

class FormTemplate():
    def __init__(self, name, form_image, questions):
        self.name = name # name of data table
        self.form_image = form_image # path to image
        self.questions = questions # list of Question

class Question():
    def __init__(self, name, question_type, responses):
        self.name = name # name of column in data table
        self.question_type = question_type # QuestionType
        self.responses = responses # list of Response

class Response():
    def __init__(self, name, location):
        self.name = name # meaning of region
        self.location =  location # Location; location within the form image

class Location():
    def __init__(self, x, y, width, height):
        self.width = width # width of bounding rectangle
        self.height = height # height of bounding rectangle
        self.x = x # x coordinate
        self.y = y # y coordinate



############################
### Processed Form Model ###
############################

class ProcessedForm():
    def __init__(self, form_template, input_image, aligned_image, annotated_image, answers):
        self.form_template = form_template
        self.input_image = input_image # path to uploaded image
        self.aligned_image = aligned_image # path to input_image after alignment
        self.annotated_image = processed_image # path to aligned_image after OMR annotation
        self.answers = answers # list of Answer objects

class Answer():
    def __init__(self, question_name, status, value, processed_image_region):
        self.question_name = question_name
        self.status = status # AnswerStatus
        self.value = value
        self.processed_image_region = processed_image_region # path to image

#############
### Enums ###
#############
class QuestionType(Enum):
    Checkbox = 1
    RadioButton = 2

class AnswerStatus(Enum):
    NeedsRevision = 0
    Resolved = 1
    Editted = 2
