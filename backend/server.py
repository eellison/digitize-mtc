from app import *
from flask import Flask, flash, request, redirect, render_template
import argparse
import webbrowser
import json
from flask import jsonify, Response
import os
import sys
from scripts import *
import time
import cv2
from math import inf

ALIGNED = False

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'],
                               filename)

@app.route('/')
def home():
    return render_template('home.html')

# TODO: template upload based on form id, and use that to retreive
# name and json
def getFormName(json_path):
    if json_path == 'anc_pg_1.json':
        return "Antenatal Record"
    elif json_path == 'delivery_pg_1.json':
        return "Delivery Page 1"
    elif json_path == 'delivery_pg_2.json':
        return "Delivery Page 2"
    assert False, "need to add another condition"

# SUD:
# [TODO] Dictionary of "form name" \to "template python forms" created when main is called
# [TODO] write_to_csv will concatenate data from each page of the form.

# DAN:
# [TODO] when page icon click cancel previous requestLiveFeedResponse calls
# [TODO] on edit annotation page, have buttons to click between pages (ex. $('#process-form-btn').click(), with updated current_page var)



@app.route('/basic_info/<json_path>', methods=['GET', 'POST'])
def basic_info(json_path):
    # TODO add parameters for form name and json path
    return render_template('basic-info.html', form_name=getFormName(json_path), json_path = json_path)


@app.route('/settings/')
def settings():
    return render_template('settings.html')



@app.route('/upload_page/<json_path>', methods=['GET', 'POST'])
def upload_form(json_path):
    template = templates[json_path]
    form_name = template["name"]
    num_pages = len(template["pages"])
    return render_template('upload_ANC_form.html', form_name=form_name, num_pages=num_pages, json_path=json_path)

# AJAX request with uploaded file
## IDEA: create a version of this that is also checking the global variable
# "success_from_live_stream", which indicates that the camera caught a
# successfully aligned live stream frame
@app.route('/upload_and_process_file/<template_json>', methods=['POST'])
def get_anc_response(template_json):
    # import pdb; pdb.set_trace()
    try:
        # import pdb; pdb.set_trace()
        return get_processed_file_json('upload_ANC_form.html', template_json)
    except AlignmentError as err:
        return jsonify(
            error_msg = err.msg,
            status = 'error'
        )

## IDEA: create a version of this that works w/o file.filename
# but jumps to the part where the file is already written (ie in live stream case)
def get_processed_file_json(html_page, template_json):
    if request.method == 'GET':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_location) # save uploaded file
            json_template_location = str(Path.cwd() / "backend" / "forms" / "json_annotations" / template_json)
            output_location = str(Path.cwd() / "backend" / "output")
            # Below: process, encode, and return the uploaded file
            start = time.time()
            processed_form = process(upload_location, json_template_location, app.config['OUTPUT_FOLDER'])
            encoder = FormTemplateEncoder()
            encoded_form = encoder.default(processed_form)
            encoded_form['status'] = "success"
            end = time.time()
            print("\n\n\n It took %.2f to run the process script." % (end-start))
            return jsonify(encoded_form)
    return render_template(html_page)


@app.route('/save/<file>', methods=['POST'])
def save_response(file):
    try:
        # NOTE: form is an array of jsons
        # TODO: fix decode_form to take in the array of JSONs and convert to Python model
        # form = decode_form(json.loads(request.data))
        # TODO: write_form_to_csv should take in a file name (ex. delivery) and an array of jsons
        # and should append a row to file.csv with concatenated jsons from array.
        # write_form_to_csv(file, form)

        # decoded_form = decode_form(json.loads(request.data))
        # write_form_to_csv(decoded_form)
        return jsonify(status='success')
    except AlignmentError as err:
        return jsonify(error_msg=err.msg, status='error')

# Capture live stream via OpenCV
# TODO: (sud) select video feed based on selection on frontend
class Camera(object):
    def __init__(self):
        # cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        cap = cv2.VideoCapture(1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 11111)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 11111)
        test, frame = cap.read()
        print("Cam Connection Test Passed: " + str(test))
        self.stream = cap

_input = 0
def write_prediction(image, align_score, blurry_score):
    global _input
    cv2.imwrite("./_input" + str(_input) + "_align_" + str(align_score) + "_blur_" + str(blurry_score) + ".png", image)
    _input += 1


def json_status(status_str, remaining_frames):
    resp = {}
    resp["status"] = status_str
    resp["remaining_frames"] = remaining_frames
    return jsonify(resp)

def reset_globals():
    global good_frames_captured
    global best_aligned_image
    global best_align_score
    good_frames_captured = 0
    best_aligned_image = None
    best_align_score = inf
    return None


@app.route('/check_alignment/<form_name>/<page_number>', methods=['GET', 'POST'])
def video_feed(form_name, page_number):
    global cam
    global sec_btw_captures
    global good_frames_captured
    global good_frames_to_capture_before_processing
    global best_aligned_image
    global best_align_score

    time.sleep(sec_btw_captures) # wait before processing frame

    template = templates[form_name]["pages"][int(page_number)]
    template_image = templates[form_name]["images"][int(page_number)]

    try:
        start = time.time()
        ret, live_frame = cam.stream.read()
        # print(live_frame)
        # cv2.imwrite("test_image.jpg", live_frame)
        aligned_image, aligned_diag_image, h, align_score = align.align_images(live_frame, template_image)
        # Uncomment the line below for live alignment debug in console
        print("Good Alignment!")
        is_blurry, blurry_score = compute_blurriness(aligned_image)
        # Uncomment to write out image with align_score & blurry_score
        # write_prediction(aligned_image, align_score, blurry_score)
        if is_blurry:
            good_frames_captured = 0
            print("Too blurry", blurry_score)
            return json_status("unaligned", None)

        if not is_blurry:
            good_frames_captured = good_frames_captured + 1
            # because it is difficult to combine alignment & blurriness
            # into one heuristic just use best alignment score for now.
            if align_score < best_align_score:
                best_align_score = align_score
                best_aligned_image = aligned_image

            if good_frames_captured < good_frames_to_capture_before_processing:
                num_remaining_frames = good_frames_to_capture_before_processing - good_frames_captured
                remaining_frames_str = str(num_remaining_frames - 1) if num_remaining_frames != 1 else "Processing..."
                return json_status("aligned", remaining_frames_str)
            else:
                # Run mark recognition on aligned image
                answered_questions, clean_input = omr.recognize_answers(best_aligned_image, template_image, template)
                # Write output
                aligned_filename = util.write_aligned_image("original_frame.jpg", aligned_image)
                # Create Form object with result, and JSONify to be sent to front end
                processed_form = Form(template.name, aligned_filename, template.w, template.h, answered_questions)
                encoder = FormTemplateEncoder()
                encoded_form = encoder.default(processed_form)
                encoded_form['status'] = "success"
                end = time.time()
                print("\n\n\n It took %.2f to run the process script." % (end-start))
                # Reset the global counters
                reset_globals()
                return jsonify(encoded_form)

    except AlignmentError as err:
        reset_globals()
        # Uncomment the line below for live alignment debug in console
        print("Alignment Error!")
        return json_status("unaligned", None)

def upload_all_templates():
    # Populate the "templates" and "template_images" Python dictionaries with
    # modeled Python "Form" objects
    global templates

    # TODO: create a loop that loads all files *.json from forms/json_annotations
    file_name = "delivery"
    path_to_json_file = str(Path.cwd() / "backend" / "forms" / "json_annotations" / (file_name + ".json"))
    templates[file_name] = read_multipage_json_to_form(path_to_json_file)

# Set up global variables
cam = Camera()
sec_btw_captures = 1
good_frames_captured = 0
good_frames_to_capture_before_processing = 5
best_aligned_image = None
best_align_score = inf # lower alignment score is better
templates = {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', const=1, type=int, default=8000)
    args = parser.parse_args()
    upload_all_templates()
    webbrowser.open('http://localhost:' + str(args.port))
    app.run(host='0.0.0.0', port=args.port)
