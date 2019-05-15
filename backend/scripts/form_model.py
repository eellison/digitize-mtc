# Model for annotating forms
import json as JSON
from enum import Enum
from copy import deepcopy





###########################
### Form Template Model ###
###########################

class Form():
    def __init__(self, name, form_image, questions):
        self.name = name # name of data table
        self.form_image = form_image # path to image
        self.questions = questions # list of Question

class Question():
    def __init__(self, name, question_type, response_regions, answer, answer_status):
        self.name = name # name of column in data table
        self.question_type = question_type # QuestionType
        self.response_regions = response_regions # list of ResponseRegion
        self.answer = answer # value that will eventually go into this column
        self.answer_status = answer_status # AnswerStatus

class ResponseRegion():
    def __init__(self, name, x, y, width, height, value):
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
    Checkbox = 1
    RadioButton = 2

class AnswerStatus(Enum):
    NotAnswered = -1
    NeedsRevision = 0
    Resolved = 1
    Editted = 2

# Enum for checkbox state
class CheckboxState(Enum):
    Unknown = -1
    Empty = 0
    Checked = 1
    Filled = 2



############################
### Processed Form Model ###
############################

# class ProcessedForm():
#     def __init__(self, form_template, input_image, matched_image, aligned_image, annotated_image, answers):
#         self.form_template = form_template
#         self.input_image = input_image # path to uploaded image
#         self.matched_image = matched_image # path to diagnostic match image
#
#
#         self.aligned_image = aligned_image # remove path to input_image after alignment
#         self.annotated_image = annotated_image # path to aligned_image after OMR annotation
#
#
#         self.answers = answers # list of Answer objects
#
# class Answer():
#     def __init__(self, question_name, status, value, processed_responses, processed_image_region):
#         self.question_name = question_name
#         self.status = status # AnswerStatus
#         self.value = value # What will go in the data table
#         self.processed_responses = processed_responses # List of ProcessedResponse
#         self.processed_image_region = processed_image_region # path to image
#
# class ProcessedResponse():
#     def __init__(self, response, value):
#         self.response = response # Response object
#         self.value = value # value associated with this response
