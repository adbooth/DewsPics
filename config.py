""" config.py
"""
from os import environ, urandom

# From environment
DEBUG = environ['DEBUG']
PYTHONUNBUFFERED = environ['PYTHONUNBUFFERED']
MONGO_URI = environ['MONGODB_URI']
PASSWORD = environ['PASSWORD']
if 'SECRET_KEY' not in environ:
    SECRET_KEY = urandom(24)

# Constants
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg']
INDEX_FILE = 'image_index.json'
