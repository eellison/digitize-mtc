from flask import Flask

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = "" # TODO
