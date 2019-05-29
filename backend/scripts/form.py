from enum import Enum

###########################
### Form Template Model ###
###########################
class Form():
    def __init__(self, name, image, width, height, question_groups):
        self.name = name # name of data table
        self.image = image # path to image of form
        self.w = width
        self.h = height
        self.question_groups = question_groups # list of QuestionGroup

class QuestionGroup():
    def __init__(self, name, x, y, width, height, questions):
        self.name = name
        self.w = width
        self.h = height
        self.x = x
        self.y = y
        self.questions = questions # list of Question

class Question():
    def __init__(self, name, question_type, response_regions, answer_status):
        self.name = name # name of column in data table
        self.question_type = question_type # QuestionType
        self.response_regions = response_regions # list of ResponseRegion
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
    # These names correspond to HTML form input types
    checkbox = 1
    radio = 2
    text = 3

class AnswerStatus(Enum):
    unresolved = -1
    resolved = 1
    editted = 2

# Enum for checkbox state
class CheckboxState(Enum):
    unknown = -1
    empty = 0
    checked = 1
