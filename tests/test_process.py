import argparse
from backend.scripts import process, util, form, omr, encoder
import glob
import pandas as pd
from pathlib import Path
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
    return processed_form

def get_ground_truth_for_form(form_name):
    ground_truth_file_name = form_name + "_ground_truth.json"
    ground_truth_json_path = str(Path.cwd() / "tests" / "ground_truth" / ground_truth_file_name)
    ground_truth_form = util.read_json_to_form(ground_truth_json_path)
    return ground_truth_form

def evaluate_results(processed_form, eval_fields):
    form_name = str(Path(processed_form.image).stem)
    ground_truth_form = get_ground_truth_for_form(form_name)
    ground_truth_answers = get_answers_from_form(ground_truth_form)
    processed_answers = get_answers_from_form(processed_form)
    assert(len(ground_truth_answers) == len(processed_answers))

    eval_dict = dict.fromkeys(eval_fields, None)
    eval_dict['test_form_name'] = form_name
    eval_dict['num_questions'] = len(ground_truth_answers)

    num_incorrect = 0
    incorrect = []
    for question, answer in processed_answers.items():
        if answer != ground_truth_answers[question]:
            incorrect.append(question)
            num_incorrect += 1
    eval_dict['num_incorrect'] = num_incorrect
    eval_dict['incorrect_names'] = tuple(incorrect)
    return(eval_dict)

def get_answers_from_form(form_object):
    answers = {}
    for question_group in form_object.question_groups:
        for question in question_group.questions:
            for response_region in question.response_regions:
                question_region_name = question_group.name + '_' + question.name
                if response_region.name:
                    question_region_name += '_' + response_region.name
                question_value = response_region.value
                answers[question_region_name] = question_value
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
    eval_fields = ['test_form_name', 'run_id', 'num_questions',
                     'num_incorrect', 'incorrect_names','num_radio_incorrect'
                     'num_checkbox_incorrect', 'num_text_incorrect',
                     'process_method_time']
    processed_forms = [process_test_form(test_form) for test_form in test_forms]
    evaluation_dicts = [evaluate_results(processed_form, eval_fields)
        for processed_form in processed_forms]
    evaluation_df = pd.DataFrame(evaluation_dicts, columns=eval_fields)

    print(evaluation_df.to_string(index=False))

if __name__ == '__main__':
    main()
