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

@app.route('/upload_page/<json_path>', methods=['GET', 'POST'])
def upload_form(json_path):
    # TODO add parameters for form name and json path
    return render_template('upload_ANC_form.html', form_name=getFormName(json_path), json_path = json_path)

# AJAX request with uploaded file
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

def get_processed_file_json(html_page, template_json):
    if request.method == 'POST':
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


@app.route('/save', methods=['POST'])
def save_response():
    try:
        decoded_form = decode_form(json.loads(request.data))
        write_form_to_csv(decoded_form)
        return jsonify(status='success')
    except AlignmentError as err:
        return jsonify(error_msg=err.msg, status='error')


# Capture video via cv2
class Camera(object):
    def __init__(self):
        cap = cv2.VideoCapture(1)
        self.stream = cap

    def get_frame_for_frontend(self):
        '''
        Returns: an open JPEG file
        '''
        ret, frame = self.stream.read()
        # Reduce size of frame to send to frontend
        small_frame_for_frontend = cv2.resize(frame, (832, 468))
        # rotate frame to vertical, 3 times counterclockwise
        rotated_frame = np.rot90(small_frame_for_frontend, 3)
        # Crop top bit because it contains part of the webcam's frame
        # TODO (sud): find a way to avoid having to do this!
        final_frame = rotated_frame[100:, :]
        frame_file_name = "current_frame.jpg"
        cv2.imwrite(frame_file_name, final_frame)
        return open(frame_file_name, 'rb').read()

    def get_raw_frame(self):
        ret, frame = self.stream.read()
        return frame

# Continuously generate frames for frontend
def gen(camera):
    while True:
        # Capture frame-by-frame
        frame = camera.get_frame_for_frontend()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Stream from web cam
@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', const=1, type=int, default=8000)
    args = parser.parse_args()
    webbrowser.open('http://localhost:' + str(args.port))
    app.run(host='0.0.0.0', port=args.port)
