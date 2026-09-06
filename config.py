# config.py

import os
# We define the project's base directory (where config.py lives)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # FIX: Explicitly join the database path to include the 'instance' folder.
    # Flask-SQLAlchemy will look for/create the 'instance' directory first.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'lokbandhu.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False