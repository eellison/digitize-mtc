import os
from os import listdir
import argparse
import csv
import sys
from collections import namedtuple

sys.path.append("..") # Adds higher directory to python modules path so we can import
from scripts import util, AlignmentError, align, compute_blurriness, omr, Form
from server import templates, upload_all_templates, get_template_and_template_image

# TODO: confusion matrix
EvaluationResults = namedtuple('EvaluationResults', ['checkbox_correct', 'checkbox_incorrect', 'radio_correct', 'radio_incorrect'])

def get_results_directory(results_file):
    results_dirs = []
    with open(results_file) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        reader_iter = iter(reader)
        first_row = next(reader_iter)
        assert first_row[-1] == "All_Forms_Pdf"
        for row in reader_iter:
            results_dirs.append("/".join(row[-1].split("/")[0:-1]))
    return results_dirs

# TODO: separate out the ranking logic of when to accept an image in server.py
def rank_stream(stream, template_image):
    aligned_image = None
    try:
        frame = util.read_image(str(stream))
        assert frame is not None
        aligned_image, aligned_diag_image, h, align_score = align.global_align(frame, template_image)

        is_blurry, blurry_score = compute_blurriness(aligned_image)
        if is_blurry:
            align_score = inf
    except AlignmentError:
        align_score = inf

    return align_score, aligned_image

def process_result_dir(form_name, result_dir, form_pages, results_map):
    files = listdir(result_dir)

    checkbox_correct = 0
    checkbox_incorrect = 0
    radio_correct = 0
    radio_incorrect = 0

    for i in range(len(form_pages['pages'])):
        template, template_image = get_template_and_template_image(form_name, i)
        streams = filter(lambda x: x.startswith("page_" + str(i)), files)
        streams = [result_dir + "/" + x for x in streams]
        streams_with_scores = [(x, *rank_stream(x, template_image)) for x in streams]
        ranked_streams = sorted(streams_with_scores, key=lambda x: x[1])
        best_stream = ranked_streams[0]
        aligned_image = best_stream[2]
        answered_questions, clean_input = omr.recognize_answers(aligned_image, template_image, template)

        # not used
        aligned_filename = None
        processed_form = Form(template.name, aligned_filename, template.w, template.h, answered_questions)
        questions = [q for group in processed_form.question_groups for q in group.questions]
        filtered_questions = [q for q in questions if q.question_type == "radio" or q.question_type == "checkbox"]
        radio_results = {}
        checkbox_results = {}
        for question in filtered_questions:
            if question.question_type == "radio":
                radio_results[question.name] = util.extract_answer(question)
            else:
                checkbox_results[question.name] = util.extract_answer(question)

        actual_results = results_map[result_dir]

        for name, predicted_answer in radio_results.items():
            real_answer = actual_results[name]
            radio_correct += real_answer == predicted_answer
            radio_incorrect += real_answer != predicted_answer

        for name, predicted_answer in checkbox_results.items():
            predicted_answer = str(predicted_answer)
            real_answer = str(actual_results[name])
            checkbox_correct += real_answer == predicted_answer
            checkbox_incorrect += real_answer != predicted_answer

    return EvaluationResults(radio_correct=radio_correct, radio_incorrect=radio_incorrect, checkbox_correct=checkbox_correct, checkbox_incorrect=checkbox_incorrect)

def map_results_file(results_file):
    results_map = {}
    with open(results_file) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        reader_iter = iter(reader)
        first_row = next(reader_iter)
        assert first_row[-1] == "All_Forms_Pdf"
        for row in reader_iter:
            directory_map = {}
            for i in range(len(row) - 1):
                directory_map[first_row[i]] = row[i]
            results_map["/".join(row[-1].split("/")[0:-1])] = directory_map

    return results_map

def run_end_to_end(results_file):
    results_dirs = get_results_directory(results_file)
    form_name = results_file.split("/")[-1].split(".")[0]
    upload_all_templates()

    results_map = map_results_file(results_file)

    form_pages = templates[form_name]

    checkbox_correct = 0
    checkbox_incorrect = 0
    radio_correct = 0
    radio_incorrect = 0
    for result_dir in results_dirs:
        eval_result = process_result_dir(form_name, result_dir, form_pages, results_map)
        checkbox_correct += eval_result.checkbox_correct
        checkbox_incorrect += eval_result.checkbox_incorrect
        radio_correct += eval_result.radio_correct
        radio_incorrect += eval_result.radio_incorrect

    print('''
    """"""""""""""
    CHECKBOX CORRECT: {}
    CHECKBOX INCORRECT: {}
    RADIO CORRECT: {}
    RADIO INCORRECT: {}
    """"""""""""""
    '''.format(checkbox_correct, checkbox_incorrect, radio_correct, radio_incorrect))

def main():
    """
    Takes in a csv file of correctly saved results generated through running digitize with
    debug saving enabled.

    Example usage:
        python backend/server.py --upload_folder /digitize-mtc/backend/output/ --save-debug
        ...
        run digitiz with the delivery form a number of times
        ...
        python test_end_to_end.py --INPUT_FILE /digitize-mtc/backend/output/delivery.csv
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--INPUT_FILE", type=str)
    args = parser.parse_args()
    result_file = args.INPUT_FILE
    if result_file is None or result_file[-4:] != ".csv":
        raise Exception("Expected csv input file found {}".format(result_file))
    run_end_to_end(result_file)

if __name__ == '__main__':
    main()
