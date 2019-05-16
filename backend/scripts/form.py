from enum import Enum

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
