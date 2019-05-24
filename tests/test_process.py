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

PARAM_NAMES = ['BLACK_LEVEL', 'FILL_THR', 'CHECK_THR', 'EMPTY_THR',
    'MAX_FEATURES', 'GOOD_MATCH_PERCENT', 'AVG_MATCH_DIST_CUTOFF']

def process_test_form(test_form_info, param_combo):
    param_values = set_omr_and_align_params(param_combo)
    form_path = test_form_info[0]
    json_annotation_path = test_form_info[1]

    # Run and time mark recognition and alignment scripts.
    start = time.time()
    input_image = util.read_image(form_path)
    template = util.read_json_to_form(json_annotation_path)
    template_image = util.read_image(template.image)
    aligned_image, aligned_diag_image, h = align.align_images(input_image, template_image)
    answered_questions, clean_input = omr.recognize_answers(aligned_image, template_image, template)
    end = time.time()

    processed_form = Form(template.name, form_path, template.w, template.h, answered_questions)
    process_time = end - start
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
    return OrderedDict(zip(PARAM_NAMES, [omr.BLACK_LEVEL, omr.FILL_THR, omr.CHECK_THR, omr.EMPTY_THR,
        align.MAX_FEATURES, align.GOOD_MATCH_PERCENT, align.AVG_MATCH_DIST_CUTOFF]))

def get_ground_truth_for_form(form_name):
    ground_truth_file_name = form_name + "_ground_truth.json"
    ground_truth_json_path = str(Path.cwd() / "tests" / "ground_truth" / ground_truth_file_name)
    ground_truth_form = util.read_json_to_form(ground_truth_json_path)
    return ground_truth_form

def get_questions(processed_form):
    form_name = str(Path(processed_form.image).stem)
    ground_truth_form = get_ground_truth_for_form(form_name)
    ground_truth_answers = get_answers_from_form(ground_truth_form)
    processed_answers = get_answers_from_form(processed_form)
    assert(len(ground_truth_answers) == len(processed_answers))

    questions = []
    for question_region_name, answer_info in processed_answers.items():
        question, value = answer_info
        ground_truth_answer = ground_truth_answers[question_region_name][1]
        #if value != ground_truth_answer:
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
    radio = questions_df[questions_df['question_type']=='radio']
    checkbox = questions_df[questions_df['question_type']=='checkbox']
    radio_confusion = pd.crosstab(radio['ground_truth_answer'], radio['reported_answer'])
    checkbox_confusion = pd.crosstab(checkbox['ground_truth_answer'], checkbox['reported_answer'])
    return(radio_confusion, checkbox_confusion)

def evaluate_results(process_results, summary_fields):
    run_id = process_results[0]
    processed_form = process_results[1][0]
    process_time = process_results[1][1]
    param_values = process_results[1][2]

    questions_df = get_questions(processed_form)
    radio_cf, checkbox_cf = get_confusion_matrices(questions_df)

    summary_dict = dict.fromkeys(summary_fields, None)
    summary_dict['form_name'] = str(Path(processed_form.image).stem)
    summary_dict['num_questions'] = len(questions_df)
    summary_dict['num_incorrect'] = len(questions_df)-(sum(list(questions_df['ground_truth_answer']==questions_df['reported_answer'])))
    summary_dict['param_values'] = tuple(param_values.values())
    summary_dict['omr_and_align_elapsed_time'] = process_time
    summary_dict['radio_conf_matrix'] = radio_cf
    summary_dict['checkbox_conf_matrix'] = checkbox_cf
    summary_dict['run_id'] = run_id
    return(summary_dict)

def get_answers_from_form(form_object):
    answers = {}
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
    # TODO(ete444): Validate parameter ranges.
    param_ranges = dict((param, vars(args)[param]) for param in PARAM_NAMES
        if vars(args)[param] is not None)
    param_combos = itertools.product(*[range for range in param_ranges.values()])
    param_combo_dicts = [dict(zip(param_ranges.keys(), combo)) for combo in param_combos]
    return param_combo_dicts

def confusion_matrix(summary_dicts, question_type_str):
    vals = ['Unknown', 'Empty', 'Checked', 'Filled']
    pairs = list(itertools.product(vals, vals))

    confusion_df = pd.DataFrame('', index=np.arange(4), columns=vals)
    confusion_df['ground_truth_answer'] = vals
    confusion_df = confusion_df.set_index('ground_truth_answer')

    confusion_dict = {pair: '' for pair in pairs}
    for summary_dict in summary_dicts:
        run_id = summary_dict['run_id']
        conf_matrix = summary_dict[question_type_str]
        for index, row in conf_matrix.iterrows():
            for col, val in dict(row).items():
                confusion_dict[(index, col)] += ('(run_id={}) {}\n'.format(run_id, val))

    for key, val in confusion_dict.items():
        index = str(key[0])
        col = str(key[1])
        confusion_df.loc[index][col] = val
    return confusion_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="to do")
    parser.add_argument("--BLACK_LEVEL", help="to do", type=param_range)
    parser.add_argument("--FILL_THR", help="to do", type=param_range)
    parser.add_argument("--CHECK_THR", help="to do", type=param_range)
    parser.add_argument("--EMPTY_THR", help="to do", type=param_range)
    parser.add_argument("--MAX_FEATURES", help="to do", type=param_range)
    parser.add_argument("--GOOD_MATCH_PERCENT", help="to do", type=param_range)
    parser.add_argument("--AVG_MATCH_DIST_CUTOFF", help="to do", type=param_range)
    args = parser.parse_args()

    param_combos = process_threshold_parameters(args)
    test_forms = get_test_form_info()

    process_results = []
    for test_form in test_forms:
        for param_combo in param_combos:
            process_results.append(process_test_form(test_form, param_combo))

    display_fields = ['run_id', 'form_name', 'param_values', 'num_questions',
        'num_incorrect', 'omr_and_align_elapsed_time']
    summary_dicts = [evaluate_results(process_result, display_fields)
        for process_result in enumerate(process_results)]

    summary_df = pd.DataFrame(summary_dicts, columns=display_fields)
    print('\n SUMMARY')
    print(tabulate(summary_df, list(summary_df.columns), tablefmt="fancy_grid"))

    radio_confusion_matrix = confusion_matrix(summary_dicts, 'radio_conf_matrix')
    print('\n RADIO CONFUSION MATRIX')
    print(tabulate(radio_confusion_matrix, list(radio_confusion_matrix.columns), tablefmt='fancy_grid'))

    #radio_confusion = pd.DataFrame({},)
    #for summary_dict in summary_dicts:
    #    radio_cf = summary_dict['radio_cf']
    #    checkbox_cf = summary_dict['checkbox_cf']
    #    print("\n Form: {}, Params: {}".format(summary_dict['form_name'], summary_dict['param_values']))
    #    print(tabulate(radio_cf, list(radio_cf.columns), tablefmt='fancy_grid'), '\t\t',tabulate(checkbox_cf, list(checkbox_cf.columns), tablefmt='fancy_grid'))


    #if args.verbose:
    #    print('\n')
    #    print('ERRORS DETAIL:')
    #    print(tabulate(errors_df, list(errors_df.columns), tablefmt="fancy_grid"))

    #radio = errors_df[errors_df['question_type'] == 'radio']
    #print('\n')
    #print("RADIO QUESTION CONFUSION TABLES")
    #for form in set(radio['form_name']):
    #    temp = radio[radio['form_name']==form]
    #    by_param = temp.groupby('param_values')
    #    print('groups: ', len(by_param.groups))
    #    dfs_by_param = [by_param.get_group(x) for x in by_param.groups]
    #    for df in dfs_by_param:
    #        radio_confusion = pd.crosstab(df['ground_truth_answer'], df['reported_answer'])
    #        print("TEST FORM, PARAM_VALUES: ", form, set(df['param_values']))
    #        print(tabulate(radio_confusion, list(radio_confusion.columns), tablefmt='fancy_grid'))

if __name__ == '__main__':
    main()
