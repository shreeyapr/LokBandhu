# routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from models.db_models import User, db
from flask import session
from utils.translations import get_translation
from utils.email_service import (
      send_welcome_email,
      send_login_email,
      send_logout_email,
      send_failed_login_email,
  )

#from app import db # Assuming db is initialized in app.py and imported


# Define the Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If the user is already logged in, redirect them to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('citizen.dashboard')) # Will define citizen blueprint later

    if request.method == 'POST':
        # Get data from the registration form
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        # Check if user already exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.register'))

        # Create new User object (default role is 'Citizen' as per model)
        new_user = User(name=name, email=email, phone=phone)
        new_user.set_password(password) # Use the hashed password method

        # Add to database and commit
        try:
            db.session.add(new_user)
            db.session.commit()
            send_welcome_email(new_user.email, new_user.name)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')

    # Render the registration page for GET request
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to the appropriate dashboard
    if current_user.is_authenticated:
        if current_user.role == 'Admin':
            return redirect(url_for('admin.admin_dashboard')) # Will define admin blueprint later
        return redirect(url_for('citizen.dashboard')) # Will define citizen blueprint later

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user) # Log the user in using Flask-Login
            send_login_email(user.email, user.name)
            flash(f'Logged in successfully as {user.role}.', 'success')
            
          
            if user.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('citizen.dashboard'))
        else:
           
            flash('Invalid email or password.', 'danger')

    # Render the login page for GET request
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    if current_user.is_authenticated:
        send_logout_email(current_user.email, current_user.name)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))