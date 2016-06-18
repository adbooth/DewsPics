""" app.py
"""
import json
from calendar import timegm
from time import gmtime
from os import path

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename

# Set up app
app = Flask(__name__)
app.config.from_pyfile('config.py')

def allowed_type(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def index_add(filename, title, blurb):
    with open(app.config['INDEX_FILE'], 'r+') as indexFile:
        index = json.load(indexFile)
        index.append({
            'timestamp': timegm(gmtime()),
            'filename': filename,
            'title': title,
            'blurb': blurb
        })

        indexFile.seek(0)
        indexFile.truncate()
        json.dump(index, indexFile)


# Set up routes
@app.route('/')
def root():
    with open(app.config['INDEX_FILE'], 'r') as indexFile:
        index = json.load(indexFile)
    index.sort(key=lambda d: d['timestamp'], reverse=True)
    return render_template('root.html', index=index)


@app.route('/photo/<filename>')
def photo(filename):
    with open(app.config['INDEX_FILE'], 'r') as indexFile:
        index = json.load(indexFile)

    for image in index:
        if image['filename'] == filename: break

    return render_template('photo.html', image=image)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if 'message' in session:
        error = session['message']

    if request.method == 'POST':
        if request.form['password'] == app.config['PASSWORD']:
            session['loggedIn'] = True
            return redirect('/upload')
        else:
            session['loggedIn'] = False
            error = 'Incorrect password'

    return render_template('login.html', error=error)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'loggedIn' not in session or not session['loggedIn']:
        session['message'] = 'Not logged in'
        return redirect('/login')

    error = ''
    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'No file part'

        image = request.files['file']
        filename = image.filename
        if filename == '':
            error = 'No selected image'

        if not error and image and allowed_type(filename):
            filename = secure_filename(filename)
            image.save(path.join(app.config['UPLOAD_FOLDER'], filename))
            index_add(filename, request.form['title'], request.form['blurb'])
            return redirect('/')

    return render_template('upload.html', error=error)
