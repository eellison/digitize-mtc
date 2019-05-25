from app import *
from flask import Flask, flash, request, redirect, render_template
import argparse
import webbrowser
import json
from flask import jsonify
import os
import sys
from scripts import *


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

@app.route('/anc_upload_pg_1', methods=['GET', 'POST'])
def upload_anc_file_pg_1():
    return upload_and_process_file('upload_anc_form.html', "anc_pg_1.json")

@app.route('/delivery_upload_pg_1', methods=['GET', 'POST'])
def upload_delivery_file_pg_1():
    return upload_and_process_file('upload_delivery_form_pg_1.html', "delivery_pg_1.json")

@app.route('/delivery_upload_pg_2', methods=['GET', 'POST'])
def upload_delivery_file_pg_2():
    return upload_and_process_file('upload_delivery_form_pg_2.html', "delivery_pg_2.json")


def upload_and_process_file(html_page, template_json):
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
            # Run the OMR processing pipeline
            processed_form = process(upload_location, json_template_location, app.config['OUTPUT_FOLDER'])
            processed_filename = str(Path(filename).stem) + "_omr_debug.png"
            return redirect(url_for('processed_file', filename=processed_filename))
    return render_template(html_page)

# AJAX request with uploaded file
@app.route('/upload_and_process_file', methods=['POST'])
def get_anc_response():
    try:
        return get_processed_file_json('upload_ANC_form.html', "anc_pg_1.json")
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
            processed_form = process(upload_location, json_template_location, app.config['OUTPUT_FOLDER'])
            encoder = FormTemplateEncoder()
            encoded_form = encoder.default(processed_form)
            return jsonify(encoded_form, status="success")
    return render_template(html_page)


# AJAX request with Template data
@app.route('/template_request', methods=['POST'])
def template_request():
    # TODO - parse request, validate data, process image,
    # save template and processed image. return request status
    template = parse_request_template(request)
    return jsonify(success=True, align_image_location="temp_location")

@app.route('/upload_form')
def upload_form_page():
    return render_template('upload_form.html')

# AJAX request with Form data
@app.route('/form_request', methods=['POST'])
def form_request():
    # TODO
    template = parse_request_template(request)
    return jsonify(success=True, align_image_location="temp_location")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', const=1, type=int, default=8000)
    args = parser.parse_args()
    webbrowser.open('http://localhost:' + str(args.port))
    app.run(host='0.0.0.0', port=args.port)
