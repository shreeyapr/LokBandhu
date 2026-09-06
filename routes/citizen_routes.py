from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session # <-- added session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime
from extensions import db 
from models.db_models import Complaint, Service 
from utils.email_service import send_complaint_submitted_email

# Define the Blueprint
citizen_bp = Blueprint('citizen', __name__, url_prefix='/citizen')

# Define allowed file extensions for attachments
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Custom Decorator ---
def citizen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.role != 'Citizen':
            flash('Access denied. You do not have Citizen privileges.', 'danger')
            if current_user.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 1. Citizen Dashboard Route ---
@citizen_bp.route('/dashboard')
@login_required
@citizen_required
def dashboard():
    recent_complaints = Complaint.query.filter_by(user_id=current_user.user_id)\
                                        .order_by(Complaint.date.desc()).limit(5).all()
    total_complaints = Complaint.query.filter_by(user_id=current_user.user_id).count()
    resolved_count = Complaint.query.filter_by(user_id=current_user.user_id, status='Resolved').count()
    
    services = Service.query.order_by(Service.category, Service.service_name).all()
    
    return render_template('citizen/dashboard.html', 
                           name=current_user.name,
                           recent_complaints=recent_complaints,
                           total_complaints=total_complaints,
                           resolved_count=resolved_count,
                           services=services)

# --- 2. Service Directory Route ---
@citizen_bp.route('/services')
@login_required
@citizen_required
def services():
    services = Service.query.order_by(Service.category, Service.service_name).all()
    services_by_category = {}
    for service in services:
        if service.category not in services_by_category:
            services_by_category[service.category] = []
        services_by_category[service.category].append(service)
        
    return render_template('citizen/service_directory.html', services_by_category=services_by_category)

# --- 3. Submit Complaint Route ---
@citizen_bp.route('/submit_complaint', methods=['GET', 'POST'])
@login_required
@citizen_required
def submit_complaint():
    if request.method == 'POST':
        category = request.form.get('category')
        description = request.form.get('description')
        attachment_path = None
        
        # Handle File Upload
        attachment_file = request.files.get('attachment')
        if attachment_file and attachment_file.filename != '':
            if allowed_file(attachment_file.filename):
                filename = secure_filename(attachment_file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                attachment_file.save(file_path)
                attachment_path = os.path.join('uploads', filename).replace('\\', '/')
            else:
                 flash('Invalid file type. Allowed types: png, jpg, jpeg, pdf.', 'warning')
                 return redirect(request.url)
        
        # Create new Complaint object
        new_complaint = Complaint(
            user_id=current_user.user_id,
            category=category,
            description=description,
            attachment=attachment_path, 
            status='Submitted', 
            date=datetime.utcnow() 
        )

        try:
            db.session.add(new_complaint)
            db.session.commit()
            
            # --- EMAIL NOTIFICATION MOVED INSIDE TRY BLOCK ---
            # Now 'new_complaint' exists and has a generated ID from commit()
            send_complaint_submitted_email(
                user_email=current_user.email,
                user_name=current_user.name,
                complaint_id=new_complaint.complaint_id,
                category=category,
                description=description,
                lang=session.get('lang', 'en')
            )
            
            flash('Complaint submitted successfully and confirmation email sent!', 'success')
            return redirect(url_for('citizen.track_complaints'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during submission. Please try again.', 'danger')
            return redirect(url_for('citizen.submit_complaint'))

    categories = ['Roads & Infrastructure', 'Water & Sanitation', 'Electricity', 'Public Health', 'Other']
    return render_template('citizen/submit_complaint.html', categories=categories)

# --- 4. Track Complaints Route ---
@citizen_bp.route('/track')
@login_required
@citizen_required
def track_complaints():
    user_complaints = Complaint.query.filter_by(user_id=current_user.user_id)\
                                        .order_by(Complaint.date.desc()).all()
                                        
    return render_template('citizen/track_complaints.html', complaints=user_complaints)