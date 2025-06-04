import os
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

from app import app, db
from models import User, Portal, Credential, Download
from download_scheduler import schedule_download_job

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You need admin privileges to access this page', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if this is the first user (will be admin)
    is_first_user = User.query.count() == 0
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, is_admin=is_first_user)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/user-management')
@admin_required
def user_management():
    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/add-user', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = 'is_admin' in request.form
    
    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('user_management'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('user_management'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('user_management'))
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('user_management'))

@app.route('/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from last admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot remove admin status from the last admin user', 'danger')
        return redirect(url_for('user_management'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = 'promoted to admin' if user.is_admin else 'demoted from admin'
    flash(f'User {user.username} was {action}', 'success')
    return redirect(url_for('user_management'))

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the last admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last admin user', 'danger')
        return redirect(url_for('user_management'))
    
    # Prevent self-deletion (current logged-in user)
    if user_id == session.get('user_id'):
        flash('Cannot delete your own account while logged in', 'danger')
        return redirect(url_for('user_management'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} was deleted successfully', 'success')
    return redirect(url_for('user_management'))

@app.route('/portal-config')
@login_required
def portal_config():
    portals = Portal.query.all()
    return render_template('portal_config.html', portals=portals)

@app.route('/add-portal', methods=['POST'])
@login_required
def add_portal():
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description')
    
    if not name or not url:
        flash('Portal name and URL are required', 'danger')
        return redirect(url_for('portal_config'))
    
    if Portal.query.filter_by(name=name).first():
        flash('Portal with this name already exists', 'danger')
        return redirect(url_for('portal_config'))
    
    portal = Portal(name=name, url=url, description=description)
    db.session.add(portal)
    db.session.commit()
    
    flash(f'Portal {name} added successfully', 'success')
    return redirect(url_for('portal_config'))

@app.route('/edit-portal/<int:portal_id>', methods=['POST'])
@login_required
def edit_portal(portal_id):
    portal = Portal.query.get_or_404(portal_id)
    
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description')
    
    if not name or not url:
        flash('Portal name and URL are required', 'danger')
        return redirect(url_for('portal_config'))
    
    # Check if the updated name conflicts with another portal's name
    existing_portal = Portal.query.filter_by(name=name).first()
    if existing_portal and existing_portal.id != portal_id:
        flash('Portal with this name already exists', 'danger')
        return redirect(url_for('portal_config'))
    
    portal.name = name
    portal.url = url
    portal.description = description
    db.session.commit()
    
    flash(f'Portal {name} updated successfully', 'success')
    return redirect(url_for('portal_config'))

@app.route('/delete-portal/<int:portal_id>', methods=['POST'])
@login_required
def delete_portal(portal_id):
    portal = Portal.query.get_or_404(portal_id)
    name = portal.name
    
    db.session.delete(portal)
    db.session.commit()
    
    flash(f'Portal {name} deleted successfully', 'success')
    return redirect(url_for('portal_config'))

@app.route('/user-credentials')
@login_required
def user_credentials():
    user_id = session.get('user_id')
    portals = Portal.query.all()
    credentials = Credential.query.filter_by(user_id=user_id).all()
    return render_template('user_credentials.html', portals=portals, credentials=credentials)

@app.route('/add-credential', methods=['POST'])
@login_required
def add_credential():
    user_id = session.get('user_id')
    portal_id = request.form.get('portal_id')
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not portal_id or not username or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('user_credentials'))
    
    # Check if user already has a credential for this portal
    existing_credential = Credential.query.filter_by(user_id=user_id, portal_id=portal_id).first()
    if existing_credential:
        flash('You already have credentials for this portal. Please edit the existing one.', 'danger')
        return redirect(url_for('user_credentials'))
    
    credential = Credential(user_id=user_id, portal_id=portal_id, username=username)
    credential.set_password(password)
    
    db.session.add(credential)
    db.session.commit()
    
    flash('Credential added successfully', 'success')
    return redirect(url_for('user_credentials'))

@app.route('/edit-credential/<int:credential_id>', methods=['POST'])
@login_required
def edit_credential(credential_id):
    user_id = session.get('user_id')
    credential = Credential.query.get_or_404(credential_id)
    
    # Ensure the credential belongs to the logged-in user
    if credential.user_id != user_id:
        flash('You are not authorized to edit this credential', 'danger')
        return redirect(url_for('user_credentials'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username:
        flash('Username is required', 'danger')
        return redirect(url_for('user_credentials'))
    
    credential.username = username
    if password:  # Only update password if a new one is provided
        credential.set_password(password)
    
    db.session.commit()
    
    flash('Credential updated successfully', 'success')
    return redirect(url_for('user_credentials'))

@app.route('/delete-credential/<int:credential_id>', methods=['POST'])
@login_required
def delete_credential(credential_id):
    user_id = session.get('user_id')
    credential = Credential.query.get_or_404(credential_id)
    
    # Ensure the credential belongs to the logged-in user
    if credential.user_id != user_id:
        flash('You are not authorized to delete this credential', 'danger')
        return redirect(url_for('user_credentials'))
    
    db.session.delete(credential)
    db.session.commit()
    
    flash('Credential deleted successfully', 'success')
    return redirect(url_for('user_credentials'))

@app.route('/download-operation')
@login_required
def download_operation():
    user_id = session.get('user_id')
    credentials = Credential.query.filter_by(user_id=user_id).all()
    return render_template('download_operation.html', credentials=credentials)

@app.route('/schedule-download', methods=['POST'])
@login_required
def schedule_download():
    user_id = session.get('user_id')
    credential_id = request.form.get('credential_id')
    facility_username = request.form.get('facility_username')
    download_type = request.form.get('download_type', 'submission')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    if not credential_id or not start_date_str or not end_date_str or not facility_username:
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'All fields are required'})
        else:
            flash('All fields are required', 'danger')
            return redirect(url_for('download_operation'))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Invalid date format'})
        else:
            flash('Invalid date format', 'danger')
            return redirect(url_for('download_operation'))
    
    if start_date > end_date:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Start date must be before end date'})
        else:
            flash('Start date must be before end date', 'danger')
            return redirect(url_for('download_operation'))
    
    credential = Credential.query.get_or_404(credential_id)
    
    # Ensure the credential belongs to the logged-in user
    if credential.user_id != user_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'You are not authorized to use this credential'})
        else:
            flash('You are not authorized to use this credential', 'danger')
            return redirect(url_for('download_operation'))
    
    # Create download record
    download = Download(
        user_id=user_id,
        portal_id=credential.portal_id,
        credential_id=credential_id,
        facility_username=facility_username,
        download_type=download_type,
        start_date=start_date,
        end_date=end_date,
        status='scheduled',
        progress=0
    )
    
    db.session.add(download)
    db.session.commit()
    
    # Schedule the actual download job
    schedule_download_job(download.id)
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True, 
            'message': 'Download scheduled successfully',
            'download_id': download.id
        })
    else:
        flash('Download scheduled successfully', 'success')
        return redirect(url_for('download_history'))

@app.route('/download-history')
@login_required
def download_history():
    user_id = session.get('user_id')
    downloads = Download.query.filter_by(user_id=user_id).order_by(Download.created_at.desc()).all()
    return render_template('download_history.html', downloads=downloads)

@app.route('/api/download-status/<int:download_id>')
@login_required
def download_status(download_id):
    """API endpoint to get the current status of a download"""
    user_id = session.get('user_id')
    download = Download.query.get_or_404(download_id)
    
    # Ensure the download belongs to the logged-in user
    if download.user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Calculate estimated completion time if in progress
    estimated_completion = None
    if download.status == 'in_progress' and download.progress > 0:
        # Simple estimation based on progress and time elapsed
        elapsed_seconds = (datetime.utcnow() - download.created_at).total_seconds()
        if elapsed_seconds > 0 and download.progress > 0:
            seconds_remaining = (elapsed_seconds / download.progress) * (100 - download.progress)
            minutes_remaining = int(seconds_remaining / 60)
            if minutes_remaining > 0:
                estimated_completion = f"About {minutes_remaining} minute(s)"
            else:
                estimated_completion = "Less than a minute"
    
    return jsonify({
        'status': download.status,
        'progress': download.progress,
        'started_at': download.created_at.isoformat(),
        'updated_at': download.updated_at.isoformat(),
        'file_path': download.file_path,
        'error_message': download.error_message,
        'estimated_completion': estimated_completion,
        'download_type': download.download_type,
        'facility_username': download.facility_username
    })

@app.route('/api/portals')
@login_required
def api_portals():
    """API endpoint to get all portals"""
    portals = Portal.query.all()
    portal_list = [
        {
            'id': portal.id,
            'name': portal.name,
            'url': portal.url,
            'description': portal.description,
            'created_at': portal.created_at.isoformat()
        }
        for portal in portals
    ]
    return jsonify({'portals': portal_list})

@app.route('/api/portal/<int:portal_id>')
@login_required
def api_portal_details(portal_id):
    """API endpoint to get details of a specific portal"""
    user_id = session.get('user_id')
    portal = Portal.query.get_or_404(portal_id)
    
    # Get user's credential for this portal if it exists
    credential = Credential.query.filter_by(user_id=user_id, portal_id=portal_id).first()
    credential_info = None
    
    if credential:
        credential_info = {
            'id': credential.id,
            'username': credential.username,
            'created_at': credential.created_at.isoformat(),
            'updated_at': credential.updated_at.isoformat()
        }
    
    return jsonify({
        'portal': {
            'id': portal.id,
            'name': portal.name,
            'url': portal.url,
            'description': portal.description,
            'created_at': portal.created_at.isoformat()
        },
        'credential': credential_info
    })
