import argparse
from backend.scripts import align, form, encoder, omr, util
from collections import OrderedDict
import itertools
import numpy as np
import pandas as pd
from pathlib import Path
from tabulate import tabulate
import time


PARAMETER_NAMES = ['BLACK_LEVEL', 'FILL_THR', 'CHECK_THR', 'EMPTY_THR',
    'MAX_FEATURES', 'GOOD_MATCH_PERCENT', 'AVG_MATCH_DIST_CUTOFF']


def process_test_form(test_form_info, param_combo):
    """Runs and times mark recognition and alignment scripts for a given
    form and set of parameters. """
    param_values = set_omr_and_align_params(param_combo)
    form_path = test_form_info[0]
    json_annotation_path = test_form_info[1]

    start = time.time()
    input_image = util.read_image(form_path)
    template = util.read_json_to_form(json_annotation_path)
    template_image = util.read_image(template.image)
    aligned_image, aligned_diag_image, h, _ = align.align_images(
        input_image, template_image)
    answered_questions, clean_input = omr.recognize_answers(
        aligned_image, template_image, template)
    end = time.time()

    processed_form = form.Form(template.name, form_path, template.w,
        template.h, answered_questions)
    process_time = end - start
    return (processed_form, process_time, param_values)


def get_ground_truth_for_form(form_name):
    """Reads JSON file containing human-labeled answers for a given form. """
    ground_truth_file_name = form_name + "_ground_truth.json"
    #ground_truth_json_path = str(Path.cwd() / "tests" / "ground_truth" /
    ground_truth_json_path = str(Path.cwd() / "backend" / "tests" / "ground_truth" /
        ground_truth_file_name)
    ground_truth_form = util.read_json_to_form(ground_truth_json_path)
    return ground_truth_form


def get_questions(processed_form):
    """Given a processed form object, returns a dataframe where each row
    contains a question with its script-reported and human-reported answers. """
    form_name = str(Path(processed_form.image).stem)
    ground_truth_form = get_ground_truth_for_form(form_name)
    ground_truth_answers = get_answers_from_form(ground_truth_form)
    processed_answers = get_answers_from_form(processed_form)
    assert(len(ground_truth_answers) == len(processed_answers))

    questions = []
    for question_region_name, answer_info in processed_answers.items():
        question, value = answer_info
        ground_truth_answer = ground_truth_answers[question_region_name][1]
        question_dict = OrderedDict()
        question_dict['question_name'] = question_region_name
        question_dict['question_type'] = question.question_type
        question_dict['ground_truth_answer'] = ground_truth_answer
        question_dict['reported_answer'] = value
        question_dict['reported_answer_status'] = question.answer_status
        questions.append(question_dict)
    questions_df = pd.DataFrame(questions)
    return questions_df


def get_confusion_matrices(questions_df):
    """Generates the confusion matrix comparing script-reported vs.
    human-reported answers to a set of radio or checkbox questions. """
    radio = questions_df[questions_df['question_type']=='radio']
    checkbox = questions_df[questions_df['question_type']=='checkbox']
    radio_confusion = pd.crosstab(
        radio['ground_truth_answer'], radio['reported_answer'])
    checkbox_confusion = pd.crosstab(
        checkbox['ground_truth_answer'], checkbox['reported_answer'])
    return(radio_confusion, checkbox_confusion)


def get_answers_from_form(form_object):
    """Given a Form object, populates a dictionary of the form
    {<question_group.name>_<question.name>_<response_region.name> :
    response_region.value. } """
    answers = OrderedDict()
    for question_group in form_object.question_groups:
        for question in question_group.questions:
            for response_region in question.response_regions:
                question_region_name = question_group.name + '_' + question.name
                if response_region.name:
                    question_region_name += '_' + response_region.name
                value = response_region.value if type(response_region.value) \
                    is str else response_region.value.name
                answers[question_region_name] = (question, value)
    return answers


def get_test_form_info():
    """Searches in /tests/test_input_forms for all test input forms paths
    and associates each with the corresponding JSON annotation. """
    test_form_dir = Path.cwd() / "backend" / "tests" / "test_input_forms"
    test_form_info = []
    for subdir in test_form_dir.iterdir():
        json_annotation_stem = str(subdir.stem) + '.json'
        json_annotation = str(Path.cwd() / "backend" / "forms" /
            "json_annotations" / json_annotation_stem)
        for path in subdir.iterdir():
            test_form_info.append((str(path), json_annotation))
    return test_form_info


def param_range(arg):
    """Custom type for command line arg parameter range. """
    try:
        min, max, n = map(int, arg.split(','))
        return np.linspace(min, max, n)
    except:
        raise argparse.ArgumentTypeError(
            "Parameter ranges must specified as: --PARAM_NAME:min,max,n")


def set_omr_and_align_params(param_combo):
    """Sets threshold parameters in OMR and alignment scripts.

    TODO(ete444): Clean this up. The current approach of directly resetting
    global vars is ugly. Consider using patches from unittest library to set
    these values. """
    params = param_combo.keys()
    if 'BLACK_LEVEL' in params:
        omr.BLACK_LEVEL = param_combo['BLACK_LEVEL']
    if 'FILL_THR' in params:
        omr.FILL_THR = param_combo['FILL_THR']
    if 'CHECK_THR' in params:
        omr.CHECK_THR = param_combo['CHECK_THR']
    if 'EMPTY_THR' in params:
        omr.EMPTY_THR = param_combo['EMPTY_THR']
    if 'MAX_FEATURES' in params:
        align.MAX_FEATURES = param_combo['MAX_FEATURES']
    if 'GOOD_MATCH_PERCENT' in params:
        align.GOOD_MATCH_PERCENT = param_combo['GOOD_MATCH_PERCENT']
    if 'AVG_MATCH_DIST_CUTOFF' in params:
        align.AVG_MATCH_DIST_CUTOFF = param_combo['AVG_MATCH_DIST_CUTOFF']
    param_variables = [omr.BLACK_LEVEL, omr.FILL_THR, omr.CHECK_THR,
        omr.EMPTY_THR, align.MAX_FEATURES, align.GOOD_MATCH_PERCENT,
        align.AVG_MATCH_DIST_CUTOFF]
    return OrderedDict(zip(PARAMETER_NAMES, param_variables))


def get_all_parameter_combos(args):
    """Parses command line args for a set of desired parameter ranges. Generates
    a list of all possible parameters combinations.

    TODO(ete444): Validate parameter ranges!!! For example, need to ensure that
    FILL_THR > CHECK_THR > EMPTY_THR. """
    param_ranges = dict((param, vars(args)[param]) for param in PARAMETER_NAMES
        if vars(args)[param] is not None)
    param_combos = itertools.product(*[range for range in param_ranges.values()])
    param_combo_dicts = [dict(zip(param_ranges.keys(), combo))
        for combo in param_combos]
    return param_combo_dicts


def summarize_results(process_results):
    """Given the results of a test run (a form and set of parameters),
    returns a pandas dataframe with summary information including number of
    incorrect questions, processing time, etc. """
    run_id = process_results[0]
    processed_form = process_results[1][0]
    process_time = process_results[1][1]
    param_values = process_results[1][2]

    questions_df = get_questions(processed_form)
    radio_cf, checkbox_cf = get_confusion_matrices(questions_df)

    summary_dict = OrderedDict()
    summary_dict['form_name'] = str(Path(processed_form.image).stem)
    summary_dict['num_questions'] = len(questions_df)
    summary_dict['num_incorrect'] = len(questions_df)-sum(list(
        questions_df['ground_truth_answer']==questions_df['reported_answer']))
    summary_dict['param_values'] = tuple([round(x, 4) for x in param_values.values()])
    summary_dict['omr_and_align_elapsed_time'] = process_time
    summary_dict['radio_conf_matrix'] = radio_cf
    summary_dict['checkbox_conf_matrix'] = checkbox_cf
    summary_dict['run_id'] = run_id
    return summary_dict


def get_summary_confusion_matrix(summaries, question_type_str):
    """Generates a confusion matrix comparing script-reported vs.
    human-reported answers to a set of radio or checkbox questions, broken out
    by 'run_id'. Each run_id corresponds to a unique pairing of input form and
    parameter values. """
    vals = [enum.name for enum in form.CheckboxState]
    pairs = list(itertools.product(vals, vals))

    confusion_df = pd.DataFrame('', index=np.arange(4), columns=vals)
    confusion_df['ground_truth_answer'] = vals
    confusion_df = confusion_df.set_index('ground_truth_answer')

    confusion_dict = {pair: '' for pair in pairs}
    for summary in summaries:
        run_id = summary['run_id']
        conf_matrix = summary[question_type_str]
        for index, row in conf_matrix.iterrows():
            for col, val in dict(row).items():
                confusion_dict[(index, col)] += ('(run_id={}) {}\n'.format(
                    run_id, val))

    for key, val in confusion_dict.items():
        index = str(key[0])
        col = str(key[1])
        confusion_df.loc[index][col] = val
    return confusion_df


def print_summary_results(summary_df, radio_confusion, checkbox_confusion):
    """Formats and prints tables from three pandas dataframes:
    (I) summary results, (II) radio question confusion matrix, and (II) checkbox
    question confusion matrix. """
    print('\n SUMMARY')
    print(tabulate(summary_df, list(summary_df.columns), tablefmt="fancy_grid"))
    print('\n RADIO CONFUSION MATRIX')
    print(tabulate(radio_confusion, list(radio_confusion.columns),
        tablefmt='fancy_grid'))
    print('\n CHECKBOX CONFUSION MATRIX')
    print(tabulate(checkbox_confusion, list(checkbox_confusion.columns),
        tablefmt='fancy_grid'))


def main():
    """
    Example usage:
        python -m backend.tests.test_omr_and_align --BLACK_LEVEL=0,255,4 --EMPTY_THR=0,1,2

    To test n parameter values in the range [min,max], use '--PARAM_NAME:min,max,n'.

    Put all input form image files that you want to test in /tests/test_input_forms/.
    """
    #########################################################
    ### Parse args for OMR/alignment parameter ranges #######
    #########################################################
    parser = argparse.ArgumentParser()
    parser.add_argument("--BLACK_LEVEL", type=param_range)
    parser.add_argument("--FILL_THR", type=param_range)
    parser.add_argument("--CHECK_THR", type=param_range)
    parser.add_argument("--EMPTY_THR", type=param_range)
    parser.add_argument("--MAX_FEATURES", type=param_range)
    parser.add_argument("--GOOD_MATCH_PERCENT", type=param_range)
    parser.add_argument("--AVG_MATCH_DIST_CUTOFF", type=param_range)
    args = parser.parse_args()

    #########################################################
    ### Run processing scripts on test input forms ##########
    #########################################################
    param_combos = get_all_parameter_combos(args)
    test_forms = get_test_form_info()
    process_results = []
    for test_form in test_forms:
        for param_combo in param_combos:
            process_results.append(process_test_form(test_form, param_combo))

    #########################################################
    ### Summarize results ###################################
    #########################################################
    summaries = [summarize_results(process_result)
        for process_result in enumerate(process_results)]
    display_fields = ['run_id', 'form_name', 'param_values', 'num_questions',
        'num_incorrect', 'omr_and_align_elapsed_time']
    summary_df = pd.DataFrame(summaries, columns=display_fields)
    radio_confusion = get_summary_confusion_matrix(
        summaries, 'radio_conf_matrix')
    checkbox_confusion = get_summary_confusion_matrix(
        summaries,'checkbox_conf_matrix')

    #########################################################
    ### Output summary table and confusion matrices #########
    #########################################################
    print_summary_results(summary_df, radio_confusion, checkbox_confusion)

if __name__ == '__main__':
    main()
