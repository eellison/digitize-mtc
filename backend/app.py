import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)
app.secret_key = "secret key"

UPLOAD_FOLDER = str(Path.cwd() / 'backend' / 'uploads')
OUTPUT_FOLDER = str(Path.cwd() / 'backend' / 'output')

# Make these directories if they do not exist
def safe_makedirs(dir_name):
    try:
        os.makedirs(dir_name) # Make the directory if it doesn't exist
    except FileExistsError:
        pass # Skip Directory already exists

safe_makedirs(UPLOAD_FOLDER)
safe_makedirs(OUTPUT_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def get_output_folder():
    return app.config['OUTPUT_FOLDER']

# Makes the server re-render when local changes are made
def before_request():
    app.jinja_env.cache = {}
app.before_request(before_request)
