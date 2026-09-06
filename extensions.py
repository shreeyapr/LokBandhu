# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions globally (UNBOUND)
db = SQLAlchemy()
login_manager = LoginManager()