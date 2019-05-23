import argparse
from backend.scripts import align, util, omr, encoder
from backend.scripts.form import Form
from collections import OrderedDict
import itertools
import numpy as np
import pandas as pd
from pathlib import Path
from tabulate import tabulate
import time
import timeit

param_names = ['BLACK_LEVEL', 'FILL_THR', 'CHECK_THR', 'EMPTY_THR',
    'MAX_FEATURES', 'GOOD_MATCH_PERCENT', 'AVG_MATCH_DIST_CUTOFF']

def process_test_form(test_form_info, param_combo):
    param_values = set_omr_and_align_params(param_combo)
    form_path = test_form_info[0]
    json_annotation_path = test_form_info[1]
    # Load input image, template, and template_image
    input_image = util.read_image(form_path) # numpy.ndarray
    template = util.read_json_to_form(json_annotation_path) # Form object
    template_image = util.read_image(template.image) # numpy.ndarray
    # Run image alignment.
    aligned_image, aligned_diag_image, h = align.align_images(input_image, template_image)
    # Run mark recognition.
    answered_questions, clean_input = omr.recognize_answers(aligned_image, template_image, template)
    processed_form = Form(template.name, form_path, template.w, template.h, answered_questions)
    process_time = 0
    return (processed_form, process_time, param_values)

def set_omr_and_align_params(param_combo):
    params = param_combo.keys()
    if 'BLACK_LEVEL' in params: omr.BLACK_LEVEL = param_combo['BLACK_LEVEL']
    if 'FILL_THR' in params: omr.FILL_THR = param_combo['FILL_THR']
    if 'CHECK_THR' in params: omr.CHECK_THR = param_combo['CHECK_THR']
    if 'EMPTY_THR' in params: omr.EMPTY_THR = param_combo['EMPTY_THR']
    if 'MAX_FEATURES' in params: align.MAX_FEATURES = param_combo['MAX_FEATURES']
    if 'GOOD_MATCH_PERCENT' in params: align.GOOD_MATCH_PERCENT = param_combo['GOOD_MATCH_PERCENT']
    if 'AVG_MATCH_DIST_CUTOFF' in params: align.AVG_MATCH_DIST_CUTOFF = param_combo['AVG_MATCH_DIST_CUTOFF']
    return OrderedDict(zip(param_names, [omr.BLACK_LEVEL, omr.FILL_THR, omr.CHECK_THR, omr.EMPTY_THR,
        align.MAX_FEATURES, align.GOOD_MATCH_PERCENT, align.AVG_MATCH_DIST_CUTOFF]))

def get_ground_truth_for_form(form_name):
    ground_truth_file_name = form_name + "_ground_truth.json"
    ground_truth_json_path = str(Path.cwd() / "tests" / "ground_truth" / ground_truth_file_name)
    ground_truth_form = util.read_json_to_form(ground_truth_json_path)
    return ground_truth_form

def find_errors(processed_form):
    form_name = str(Path(processed_form.image).stem)
    ground_truth_form = get_ground_truth_for_form(form_name)
    ground_truth_answers = get_answers_from_form(ground_truth_form)
    processed_answers = get_answers_from_form(processed_form)
    assert(len(ground_truth_answers) == len(processed_answers))

    errors = []
    for question_region_name, answer_info in processed_answers.items():
        question, value = answer_info
        ground_truth_answer = ground_truth_answers[question_region_name][1]
        if value != ground_truth_answer:
            error_info = OrderedDict()
            error_info['question_name'] = question_region_name
            error_info['question_type'] = question.question_type
            error_info['ground_truth_answer'] = ground_truth_answer
            error_info['reported_answer'] = value
            error_info['reported_answer_status'] = question.answer_status
            errors.append(error_info)
    return (errors, len(ground_truth_answers))

def evaluate_results(process_results, summary_fields):
    processed_form = process_results[0]
    process_time = process_results[1]
    param_values = process_results[2]

    errors, total_num_questions = find_errors(processed_form)
    summary_dict = dict.fromkeys(summary_fields, None)
    summary_dict['form_name'] = str(Path(processed_form.image).stem)
    summary_dict['num_questions'] = total_num_questions
    summary_dict['num_incorrect'] = len(errors)
    summary_dict['param_values'] = tuple(param_values.values())
    summary_dict['process_method_time'] = process_time
    summary_dict['run_id'] = str(time.time())
    summary_dict['error_info'] = errors
    return(summary_dict)

def get_answers_from_form(form_object):
    answers = {}
    for question_group in form_object.question_groups:
        for question in question_group.questions:
            for response_region in question.response_regions:
                question_region_name = question_group.name + '_' + question.name
                if response_region.name:
                    question_region_name += '_' + response_region.name
                # TODO: Clean this up.
                value = response_region.value if type(response_region.value) is str else response_region.value.name
                answers[question_region_name] = (question, value)
    return answers

def timeit_wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

def get_test_form_info():
    test_form_dir = Path.cwd() / "tests" / "test_input_forms"
    test_form_info = []
    for subdir in test_form_dir.iterdir():
        json_annotation_stem = str(subdir.stem) + '.json'
        json_annotation = str(Path.cwd() / "backend" / "forms" / "json_annotations" / json_annotation_stem)
        for path in subdir.iterdir():
            test_form_info.append((str(path), json_annotation))
    return test_form_info

def param_range(arg):
    try:
        min, max, n = map(int, arg.split(','))
        return np.linspace(min, max, n)
    except:
        raise argparse.ArgumentTypeError("Parameter ranges must specified as: --PARAM_NAME:min,max,n")

def process_threshold_parameters(args):
    # TODO(ete444): Validate param ranges.
    param_ranges = dict((param, vars(args)[param]) for param in param_names
        if vars(args)[param] is not None)
    param_combos = itertools.product(*[range for range in param_ranges.values()])
    param_combo_dicts = [dict(zip(param_ranges.keys(), combo)) for combo in param_combos]
    return param_combo_dicts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="verbose terminal output")
    parser.add_argument("--BLACK_LEVEL", help="omr black level threshold", type=param_range)
    parser.add_argument("--FILL_THR", help="omr fill threshold", type=param_range)
    parser.add_argument("--CHECK_THR", help="omr check threshold", type=param_range)
    parser.add_argument("--EMPTY_THR", help="omr empty threshold", type=param_range)
    parser.add_argument("--MAX_FEATURES", help="omr empty threshold", type=param_range)
    parser.add_argument("--GOOD_MATCH_PERCENT", help="omr empty threshold", type=param_range)
    parser.add_argument("--AVG_MATCH_DIST_CUTOFF", help="omr empty threshold", type=param_range)
    args = parser.parse_args()

    param_combos = process_threshold_parameters(args)
    test_forms = get_test_form_info()

    process_results = []
    for test_form in test_forms:
        for param_combo in param_combos:
            process_results.append(process_test_form(test_form, param_combo))

    summary_fields = ['form_name', 'num_questions',
        'num_incorrect', 'param_values', 'process_method_time', 'run_id']
    summary_dicts = [evaluate_results(process_result, summary_fields)
        for process_result in process_results]

    error_dicts = []
    for summary_dict in summary_dicts:
        errors = summary_dict['error_info']
        for error in errors:
            error['form_name'] = summary_dict['form_name']
            error['run_id' ]= summary_dict['run_id']
            error_dicts.append(error)

    summary_df = pd.DataFrame(summary_dicts, columns=summary_fields)
    errors_df = pd.DataFrame(error_dicts)

    # 'BLACK_LEVEL', 'FILL_THR', 'CHECK_THR', 'EMPTY_THR', 'MAX_FEATURES', 'GOOD_MATCH_PERCENT', 'AVG_MATCH_DIST_CUTOFF'
    # TODO: Code Cleanup.
    print('\n')
    print('SUMMARY')
    print(tabulate(summary_df, list(summary_df.columns), tablefmt="fancy_grid"))

    if args.verbose:
        print('\n')
        print('ERRORS DETAIL:')
        print(tabulate(errors_df, list(errors_df.columns), tablefmt="fancy_grid"))

    radio = errors_df[errors_df['question_type'] == 'radio']
    print('\n')
    print("RADIO QUESTION CONFUSION TABLES")
    for form in set(radio['form_name']):
        temp = radio[radio['form_name']==form]
        radio_confusion = pd.crosstab(radio['ground_truth_answer'], radio['reported_answer'])
        print("TEST FORM: ", form)
        print(tabulate(radio_confusion, list(radio_confusion.columns), tablefmt='fancy_grid'))

if __name__ == '__main__':
    main()
