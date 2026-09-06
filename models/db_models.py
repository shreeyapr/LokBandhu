# models/db_models.py

from extensions import db # Import the SQLAlchemy object from the app module
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- User Model ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    # Columns based on SRS [cite: 20]
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # Stores the hashed password
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='Citizen') # 'Citizen' or 'Admin' [cite: 6]

    # Relationships
    complaints = db.relationship('Complaint', backref='submitter', lazy='dynamic')

    def set_password(self, password):
        """Hashes the password using Werkzeug for security """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Required by Flask-Login for session management"""
        return self.user_id
    
    def __repr__(self):
        return f"<User {self.email}>"

# --- Complaint Model ---
class Complaint(db.Model):
    __tablename__ = 'complaints'

    # Columns based on SRS [cite: 21]
    complaint_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True) # File path or URL
    status = db.Column(db.String(50), nullable=False, default='Submitted') # e.g., Submitted, In Progress, Resolved [cite: 11]
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Complaint {self.complaint_id} - Status: {self.status}>"

# --- Service Model ---
class Service(db.Model):
    __tablename__ = 'services'

    # Columns based on SRS [cite: 22]
    service_id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False) # e.g., rural, urban, metro [cite: 12]
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Service {self.service_name}>"