from .form import *
from .util import *
from .align import *

# tuned for 300 dpi grayscale text
BLACK_LEVEL = 0.5 * 255 # 255 is pure white
CHECK_THR = 0.05 # threshold for checked box
EMPTY_THR = 0.02 # threshold for empty box
RADIO_THR = 0.01 # threhold for picking radio button




def calc_checkbox_score(image, response_region):
    """
    Args:
        image (numpy.ndarray): image of whole form
        loc (ResponseRegion): describes location of checkbox
    Returns:
        scr (float): score for checkbox
    """
    w, h, x, y = (response_region.w, response_region.h, response_region.x, response_region.y)
    roi = image[y : y + h, x : x + w] < BLACK_LEVEL
    # For now, stick with simple image masking. Later refine "remove_checkbox_outline" in util.py
    # masked = roi[1:-1, 1:-1] & roi[:-2, 1:-1] & roi[2:, 1:-1] & roi[1:-1, :-2] & roi[1:-1, 2:]
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
    finetune(input_image, template_image, response_region)

    input_score = calc_checkbox_score(input_image, response_region)
    template_score = calc_checkbox_score(template_image, response_region)
    scr = input_score - template_score
    if scr > CHECK_THR:
        checkbox_state = CheckboxState.checked
    elif scr < EMPTY_THR:
        checkbox_state = CheckboxState.empty
    else:
        checkbox_state = CheckboxState.unknown
        print("Ambiguous checkbox state for %s\nScore: %.4f" % (response_region.name, scr))
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
    question.answer_status = AnswerStatus.unresolved if state == CheckboxState.unknown else AnswerStatus.resolved
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
    for rr in question.response_regions:
        finetune(input_image, template_image, rr) # finetune response region to align
        rr.value = calc_checkbox_score(input_image, rr)
    sorted_regions = sorted(question.response_regions, reverse=True, key=lambda rr: rr.value) # sort by score
    highest_score = sorted_regions[0].value
    second_highest_score = sorted_regions[1].value
    if (highest_score - second_highest_score) > RADIO_THR:
        # One box is clearly the most filled - pick it as the checked box
        for rr in sorted_regions:
            rr.value = CheckboxState.empty # set all to empty
        sorted_regions[0].value = CheckboxState.checked # update highest score to checked
        question.answer_status = AnswerStatus.resolved
    else:
        # No one box is clearly more filled than the others - set all to unknown
        print(highest_score - second_highest_score)
        for rr in question.response_regions:
            rr.value = CheckboxState.unknown
        question.answer_status = AnswerStatus.unresolved
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
        finetune(input_image, template_image, region) # finetune response region to align
        region.value = ""
    question.answer_status = AnswerStatus.unresolved
    return question

# def digits_answer(question, input_image, template_image):
#     """
#     Args:
#         question (Question): question with type QuestionType.digits
#         input_image (numpy.ndarray): image of filled form
#         template_image (numpy.ndarray): image of unfilled form template
#     Returns:
#         question (Question): same input question, with "answers" filled in
#     """
#     #
#     assert len(question.response_regions) == 1
#     rr = question.response_regions[0]
#     rr.value = ""
#     question.answer_status = AnswerStatus.unresolved
#
#     expected_number_digits = question.expected_number_digits
#     assert expected_number_digits is not None
#
#     w, h, x, y = (rr.w, rr.h, rr.x, rr.y)
#     digits_region = input_image[y : y+h, x : x+w]
#     digit_boxes = extract_digit_boxes(digits_region)
#     if len(digit_boxes) != expected_number_digits:
#         return question
#
#     digit_predictions = [predict_digit(digit) for digit in digit_boxes]
#     # TODO - only mark one digit as uncertain instead of entire answer,
#     # and refine probability cutoff. also need to figure out workflow on frontend
#     # of results
#     PROB_THRESHOLD = .6
#     if any(map(lambda digit_prob: digit_prob[1] < PROB_THRESHOLD, digit_predictions)):
#         return question
#
#     answer = "".join(map(lambda digit_prob: str(digit_prob[0]), digit_predictions))
#
#     rr.value = answer
#     question.answer_status = AnswerStatus.resolved
#     return question


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
    elif question.question_type == QuestionType.digits.name:
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
