from skimage.filters import threshold_local
import scipy.ndimage
from .form import *
from .util import remove_checkbox_outline
import cv2


# tuned for 300 dpi grayscale text
BLACK_LEVEL  = 0.8 * 255 # 255 is pure white
FILL_THR     = 0.22 # threshold for filled box
CHECK_THR    = 0.05 # threshold for checked box
EMPTY_THR    = 0.03 # threashold for empty box

def clean_image(image):
    """
    Args:
        image (numpy.ndarray): image to clean
    Returns:
        clean (numpy.ndarray): cleaned image
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    T = threshold_local(image, 11, offset=10, method="gaussian")
    clean = (image > T).astype("uint8")*255
    return clean

def calc_checkbox_score(image, response_region):
    """
    Args:
        image (numpy.ndarray): image of whole form
        loc (ResponseRegion): describes location of checkbox
    Returns:
        scr (float): score for checkbox
    """
    w, h, x, y = (response_region.w, response_region.h, response_region.x, response_region.y)
    # For now, turn off basic image masking in favor of remove_checkbox_outline
    # masked = roi[1:-1,1:-1] & roi[:-2,1:-1] & roi[2:,1:-1] & roi[1:-1,:-2] & roi[1:-1,2:]
    image = remove_checkbox_outline(image[y : y+h, x : x+w], response_region.name)
    roi = image < BLACK_LEVEL
    scr = (roi).sum() / (w * h)
    return scr

def checkbox_state(input_image, template_image, response_region):
    """
    Args:
        input_image (numpy.ndarray): target image
        template_image (numpy.ndarray): template image
        response_region (ResponseRegion): describes location of checkbox
    Returns:
        checkbox_state (CheckboxState): inferred state of this checkbox
    """

    template_score = calc_checkbox_score(template_image, response_region)
    input_score = calc_checkbox_score(input_image, response_region)
    scr = input_score # just take input score, for now
    if scr > FILL_THR:
        checkbox_state = CheckboxState.Filled
    elif scr > CHECK_THR:
        checkbox_state =  CheckboxState.Checked
    elif scr < EMPTY_THR:
        checkbox_state =  CheckboxState.Empty
    else:
        checkbox_state =  CheckboxState.Unknown
        print("Ambiguous checkbox state for %s\nScore: %.4f" % (response_region.name, input_score))
    response_region.value = checkbox_state
    return checkbox_state

def checkbox_answer(question, input_image, template_image):
    """
    Args:
        question (Question): question with type QuestionType.Checkbox
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with "answer" filled in
    """
    state = checkbox_state(input_image, template_image, question.response_regions[0])
    question.answer_status = AnswerStatus.NeedsRevision if state == CheckboxState.Unknown else AnswerStatus.Resolved
    question.answer = True if state == CheckboxState.Checked else False
    return question

def answer(question, input_image, template_image):
    """
    Args:
        question (Question): input question, to be processed based on QuestionType
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with "answer" filled in
    """
    if question.question_type == QuestionType.Checkbox.name:
        return checkbox_answer(question, input_image, template_image)
    else:
        # No logic for other question types, yet...
        print("Warning: could not process question type %s, skipping for now, " % str(question.question_type))
        return question

def recognize_answers(input_image, template_image, form):
    """
    Args:
        image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form
        form (Form): Form template, with questions unanswered
    Returns:
        answered_questions (List[Question]): questions with answers filled in
        cleaned_input (numpy.ndarray): cleaned input, useful for diagnostics
    """
    clean_input = clean_image(input_image)
    clean_template = clean_image(template_image)
    answered_questions = [answer(question, clean_input, clean_template) for question in form.questions]
    return answered_questions, clean_input
