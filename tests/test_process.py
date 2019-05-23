import argparse
from backend.scripts import process, util, form, omr, encoder
import pandas as pd
from pathlib import Path
import time
import timeit

def process_test_form(test_form_info):
    form_path = test_form_info[0]
    json_annotation_path = test_form_info[1]
    output_dir= str(Path.cwd() / "tests" / "test_process_output")

    wrapped = timeit_wrapper(process, form_path, json_annotation_path, output_dir)
    process_time = timeit.Timer(wrapped).timeit(1)

    form_file_stem = str(Path(form_path).stem)
    processed_form_path = output_dir + '/' + form_file_stem + "_processed.json"
    processed_form = util.read_json_to_form(processed_form_path)
    return (processed_form, process_time)

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
            error_info = {}
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

    errors, total_num_questions = find_errors(processed_form)
    summary_dict = dict.fromkeys(summary_fields, None)
    summary_dict['form_name'] = str(Path(processed_form.image).stem)
    summary_dict['num_questions'] = total_num_questions
    summary_dict['num_incorrect'] = len(errors)
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
                value = response_region.value
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

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    test_forms = get_test_form_info()
    summary_fields = ['form_name', 'num_questions',
        'num_incorrect', 'process_method_time', 'run_id']
    process_results = [process_test_form(test_form) for test_form in test_forms]

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
    summary_df.to_csv('tests/summary.csv', index=False)
    errors_df.to_csv('tests/errors.csv', index=False)

if __name__ == '__main__':
    main()
