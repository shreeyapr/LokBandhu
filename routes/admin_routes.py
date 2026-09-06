from functools import wraps
from flask import Blueprint, flash, redirect, render_template, url_for, request, session
from flask_login import current_user, login_required
import sys # Added for logging traceback details cleanly

# Import models and extensions
from models.db_models import Complaint, Service, User 
from extensions import db 
from utils.email_service import (
    send_complaint_status_update_email,
    send_role_changed_email,
    send_service_notification_email,
)

# Define the Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Custom Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.role != 'Admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('citizen.dashboard') if current_user.role == 'Citizen' else url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Dashboard Route ---
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='Submitted').count()
    in_progress_complaints = Complaint.query.filter_by(status='In Progress').count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    total_users = User.query.count()
    total_services = Service.query.count()

    return render_template('admin/admin_dashboard.html', 
        name=current_user.name,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints,
        total_users=total_users,
        total_services=total_services
    )

# --- Manage Complaints ---
@admin_bp.route('/complaints')
@login_required
@admin_required
def manage_complaints():
    all_complaints = Complaint.query.order_by(Complaint.date.desc()).all()
    status_options = ['Submitted', 'In Progress', 'Resolved', 'Closed (Irrelevant)']
    return render_template('admin/manage_complaints.html', complaints=all_complaints, status_options=status_options)

@admin_bp.route('/complaints/update_status/<int:complaint_id>', methods=['POST'])
@login_required
@admin_required
def update_complaint_status(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    old_status = complaint.status
    new_status = request.form.get('status')
    
    if new_status and new_status in ['Submitted', 'In Progress', 'Resolved', 'Closed (Irrelevant)']:
        try:
            complaint.status = new_status
            db.session.commit()

            # --- EMAIL NOTIFICATION MOVED HERE ---
            send_complaint_status_update_email(
                user_email=complaint.submitter.email, # lowercase 'complaint' is the instance
                user_name=complaint.submitter.name,
                complaint_id=complaint.complaint_id,
                category=complaint.category,
                old_status=old_status,
                new_status=new_status,
                lang=session.get('lang', 'en')
            )
            flash(f'Complaint status updated and email sent.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_complaints'))

# --- Manage Services ---
@admin_bp.route('/services', methods=['GET', 'POST'])
@admin_bp.route('/services/delete/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def manage_services(service_id=None):
    action = None
    target_service_name = "Unknown Service" # Set safe baseline fallback

    if request.method == 'POST':
        # --- PATHWAY A: Handle Service Deletion ---
        if service_id:
            service_obj = Service.query.get_or_404(service_id)
            # Create a localized string copy so it lives on after the model instance object drops
            target_service_name = str(service_obj.service_name)
            
            db.session.delete(service_obj)
            action = 'deleted'
            
        # --- PATHWAY B: Handle Add or Edit Forms ---
        else:
            service_id_form = request.form.get('service_id')
            form_service_name = request.form.get('service_name')
            category = request.form.get('category')
            description = request.form.get('description')
            
            target_service_name = form_service_name

            if service_id_form and service_id_form.isdigit():
                existing_service = Service.query.get(int(service_id_form))
                if existing_service:
                    existing_service.service_name = form_service_name
                    existing_service.category = category
                    existing_service.description = description
                    action = 'edited'
                else:
                    flash('Target service record to modify could not be located.', 'warning')
                    return redirect(url_for('admin.manage_services'))
            else:
                new_service = Service(service_name=form_service_name, category=category, description=description)
                db.session.add(new_service)
                action = 'added'

        # --- DATABASE TRANSACTION & NOTIFICATION CRADLE ---
        try:
            db.session.commit()
            
            # Fire email pipeline now that the database state change is locked in cleanly
            if action:
                send_service_notification_email(
                    user_email=current_user.email,
                    user_name=current_user.name,
                    action=action,
                    service_name=target_service_name, # Safeguarded string instance passed here
                    lang=session.get('lang', 'en')
                )
                flash(f'Service "{target_service_name}" {action} successfully.', 'success')
                
        except Exception as db_exception:
            db.session.rollback()
            
            # This turns on precise tracking visibility inside your terminal environment!
            print("="*60, file=sys.stderr)
            print(f"🔴 CRITICAL DATABASE ROLLBACK TRIGGERED: {db_exception}", file=sys.stderr)
            print("="*60, file=sys.stderr)
            
            # Inform user if foreign keys are blocking deletion
            if action == 'deleted':
                flash('Database error occurred: Cannot delete this service because it is currently linked to active citizen records/complaints.', 'danger')
            else:
                flash('Database error occurred: Failed to save changes. Make sure service name is unique.', 'danger')
        
        return redirect(url_for('admin.manage_services'))

    # GET Workflow processing
    all_services = Service.query.order_by(Service.category, Service.service_name).all()
    return render_template('admin/manage_services.html', services=all_services)
# --- Manage Users ---
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    all_users = User.query.filter(User.user_id != current_user.user_id).all()
    return render_template('admin/manage_users.html', users=all_users, role_options=['Citizen', 'Admin'])

@admin_bp.route('/users/update_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user_to_update = User.query.get_or_404(user_id)
    old_role = user_to_update.role
    new_role = request.form.get('role')
    
    if new_role in ['Citizen', 'Admin']:
        try:
            user_to_update.role = new_role
            db.session.commit()

            # --- EMAIL NOTIFICATION MOVED HERE ---
            send_role_changed_email(
                user_email=user_to_update.email,
                user_name=user_to_update.name,
                old_role=old_role,
                new_role=new_role,
                lang=session.get('lang', 'en')
            )
            flash(f'Role updated for {user_to_update.name}.', 'success')
        except:
            db.session.rollback()
            flash('Error updating role.', 'danger')
            
    return redirect(url_for('admin.manage_users'))