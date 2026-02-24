import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'          # if you allow profile picture upload
    # FACE_RECOGNITION_TOLERANCE = 0.6        # you can add later