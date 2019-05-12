from app import app
from flask import Flask, flash, request, redirect, render_template
import argparse
import webbrowser
from json_encoder import f as example_template
from form_model import *
import json
from flask import jsonify

@app.route('/')
def home():
    return render_template('home.html')

def parse_request_template(request):
    # todo real parsing
    return example_template


@app.route('/upload_template', methods=['GET'])
def upload_template_page():
    return render_template('upload_template.html')

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
    from json_encoder import f
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', const=1, type=int, default=8000)
    args = parser.parse_args()
    webbrowser.open('http://localhost:' + str(args.port))
    app.run(host='0.0.0.0', port=args.port)
