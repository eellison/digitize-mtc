import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)
app.secret_key = "secret key"

UPLOAD_FOLDER = str(Path.cwd() / 'backend' / 'uploads')
PROCESSED_FOLDER = str(Path.cwd() / 'backend' / 'processed')

# Make these directories if they do not exist
def safe_makedirs(dir_name):
    try:
        os.makedirs(dir_name) # Make the directory if it doesn't exist
    except FileExistsError:
        pass # Skip Directory already exists

safe_makedirs(UPLOAD_FOLDER)
safe_makedirs(PROCESSED_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
