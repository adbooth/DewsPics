""" app.py
"""
import json
from calendar import timegm
from time import gmtime
from os import path, remove

from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo, GridFS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_pyfile('config.py')
mongo = PyMongo(app)

def populate(fs):
    for imageFile in fs.find():
        filename = imageFile.filename
        filepath = path.join(app.config['UPLOAD_FOLDER'], filename)
        open(filepath, 'w').write(imageFile.read())

def getIndex(fs):
    index = []
    for imageFile in fs.find():
        index.append({
            'timestamp': imageFile.timestamp,
            'filename': imageFile.filename,
            'title': imageFile.title,
            'blurb': imageFile.blurb
        })
    return sorted(index, key=lambda d: d['timestamp'], reverse=True)

@app.route('/')
def home():
    """ Renders the photo stream. """
    fs = GridFS(mongo.db)
    populate(fs)
    return render_template('home.html', index=getIndex(fs))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    """ Renders and validates login. """
    if request.method == 'POST':
        if request.form['password'] == app.config['PASSWORD']:
            # Correct password, set session var and redirect
            session['loggedIn'] = True
            return redirect('/manage')
        else:
            # Incorrect pasword, ask to try again
            session['loggedIn'] = False
            error = 'Incorrect password'

    return render_template('login.html', error=error)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    """ Renders upload and edit page. Requires login. """
    # Check for login
    if 'loggedIn' not in session or not session['loggedIn']:
        return redirect('/login')

    # Setup
    error = ''
    fs = GridFS(mongo.db)
    populate(fs)

    # Check for POST
    if request.method == 'POST':
        # Get image file
        imageFile = request.files['image']
        filename = secure_filename(imageFile.filename)

        # Make sure file exists and is of the right type
        filetype = filename.split('.')[-1].lower()
        if filename == '':
            error = 'No file selected'
        elif not ('.' in filename and filetype in app.config['ALLOWED_EXTENSIONS']):
            error = 'Bad image filename'

        # Put image in db
        if not error:
            form = request.form
            fs.put(imageFile,
                timestamp=timegm(gmtime()),
                filename=filename,
                title=form['title'],
                blurb=form['blurb'])
            return redirect('/')

    return render_template('manage.html', index=getIndex(fs), error=error)

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    """ Renders and handles photo edit page """
    # Check for login
    if 'loggedIn' not in session or not session['loggedIn']:
        return redirect('/login')

    # Setup
    error = ''
    fs = GridFS(mongo.db)
    populate(fs)
    oldImageFile = fs.find_one({'filename': filename})

    # Check for POST
    if request.method == 'POST':
        if request.files['image'].filename == '':
            # Using old image file
            imageFile = open(path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            # Using newly uploaded image file
            imageFile = request.files['image']
            filename = secure_filename(imageFile.filename)

            # Make sure file exists and is of the right type
            filetype = filename.split('.')[-1].lower()
            if not ('.' in filename and filetype in app.config['ALLOWED_EXTENSIONS']):
                error = 'Bad image filename'

            # Delete old local file
            remove(path.join(app.config['UPLOAD_FOLDER'], oldImageFile.filename))

        # Store image on database with info
        if not error:
            form = request.form
            fs.put(imageFile,
                timestamp=oldImageFile.timestamp,
                filename=filename,
                title=form['title'],
                blurb=form['blurb'])
            # Find old image file and delete it
            fs.delete(oldImageFile._id)
            return redirect('/#%s' % filename)

    return render_template('edit.html', imageInfo={
        'filename': oldImageFile.filename,
        'title': oldImageFile.title,
        'blurb': oldImageFile.blurb
    }, error=error)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    """ Endpoint for deleting a photo """
    # Check for login
    if 'loggedIn' not in session or not session['loggedIn']:
        return redirect('/login')

    fs = GridFS(mongo.db)
    fs.delete(fs.find_one({'filename': filename})._id)
    remove(path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect('/')
