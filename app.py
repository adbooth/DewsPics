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

# Set up routes
@app.route('/')
def home():
    """ Build page with image data file sorted by timestamp """
    with open(app.config['INDEX_FILE'], 'r') as indexFile:
        index = json.load(indexFile)
    index.sort(key=lambda d: d['timestamp'], reverse=True)
    return render_template('home.html', index=index)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Show login and check password against password environment var """
    error = ''
    if request.method == 'POST':
        if request.form['password'] == app.config['PASSWORD']:
            # Correct password, set session var and redirect
            session['loggedIn'] = True
            return redirect('/upload')
        else:
            # Incorrect pasword, ask to try again
            session['loggedIn'] = False
            error = 'Incorrect password'

    return render_template('login.html', error=error)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """ Send upload page if logged in """

    if 'loggedIn' not in session or not session['loggedIn']:
        # Not logged in, send to login page
        return redirect('/login')

    error = ''
    if request.method == 'POST':
        image = request.files['file']
        filename = image.filename

        # Make sure file exists and is of the right type
        if filename == '':
            error = 'No file selected'
        elif not ('.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']):
            error = 'Bad image filename'

        if not error and image:
            # Save file
            filename = secure_filename(filename)
            image.save(path.join(app.config['UPLOAD_FOLDER'], filename))
            # Add file to index
            with open(app.config['INDEX_FILE'], 'r+') as indexFile:
                index = json.load(indexFile)
                index.append({
                    'timestamp': timegm(gmtime()),
                    'filename': filename,
                    'title': request.form['title'],
                    'blurb': request.form['blurb']
                })
                indexFile.seek(0)
                indexFile.truncate()
                json.dump(index, indexFile)
            # Redirect to home page
            return redirect('/')

    return render_template('upload.html', error=error)
