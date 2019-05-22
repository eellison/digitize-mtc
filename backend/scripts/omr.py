from .form import *
from .util import remove_checkbox_outline, clean_image, project_mark_locations
import cv2


# tuned for 300 dpi grayscale text
BLACK_LEVEL  = 0.8 * 255 # 255 is pure white
FILL_THR     = 0.22 # threshold for filled box
CHECK_THR    = 0.05 # threshold for checked box
EMPTY_THR    = 0.03 # threashold for empty box


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
        question (Question): question with type QuestionType.checkbox
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with "answer" filled in
    """
    state = checkbox_state(input_image, template_image, question.response_regions[0])
    question.answer_status = AnswerStatus.NeedsRevision if state == CheckboxState.Unknown else AnswerStatus.Resolved
    return question

def radio_answer(question, input_image, template_image):
    """
    Args:
        question (Question): question with type QuestionType.radio
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with "answers" filled in
    """
    for region in question.response_regions:
        checkbox_state(input_image, template_image, region)
    # TODO: add logic to determine the AnswerStatus based on responses
    return question

def text_answer(question, input_image, template_image):
    """
    Args:
        question (Question): question with type QuestionType.text
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with "answers" filled in
    """
    # TODO: have this run pytesseract on the input region (see "/scratch/ocr_test.py")
    for region in question.response_regions:
        region.value = "Some OCR guess at what this text should be..."
    question.answer_status = AnswerStatus.NeedsRevision
    return question

def answer(question, input_image, template_image):
    """
    Args:
        question (Question): input question, to be processed based on QuestionType
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question (Question): same input question, with responses
    """
    if question.question_type == QuestionType.checkbox.name:
        return checkbox_answer(question, input_image, template_image)
    elif question.question_type == QuestionType.radio.name:
        return radio_answer(question, input_image, template_image)
    elif question.question_type == QuestionType.text.name:
        return text_answer(question, input_image, template_image)
    else:
        # No logic for other question types, yet...
        print("Warning: could not process question type %s, skipping for now, " % str(question.question_type))
        return question

def answer_group(question_group, input_image, template_image):
    """
    Args:
        question_group (QuestionGroup): a group of question on the input Form
        input_image (numpy.ndarray): image of filled form
        template_image (numpy.ndarray): image of unfilled form template
    Returns:
        question_group (Question): same input group, with responses filled in
    """
    question_group.questions = [answer(question, input_image, template_image) for question in question_group.questions]
    return question_group

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
    form = project_mark_locations(clean_input, form)
    answered_questions = [answer_group(group, clean_input, clean_template) for group in form.question_groups]
    return answered_questions, clean_input
