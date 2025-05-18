from flask import Blueprint, render_template, url_for, redirect, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, UserRole, Patient, Doctor

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Web Routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if not all([username, email, password, confirm_password, role, first_name, last_name]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
        
        try:
            user_role = UserRole(role)
        except ValueError:
            flash('Invalid role selected.', 'danger')
            return render_template('register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            role=user_role,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        
        # Create patient or doctor profile if needed
        if user_role == UserRole.PATIENT:
            patient = Patient(user=user)
            db.session.add(patient)
        elif user_role == UserRole.DOCTOR:
            doctor = Doctor(user=user, license_number='PENDING')
            db.session.add(doctor)
        
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
        
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('auth.dashboard')
        
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role.value,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name
    }
    
    # Get role-specific data
    if current_user.role == UserRole.PATIENT and current_user.patient_profile:
        from routes.appointments import get_patient_appointments
        appointments = get_patient_appointments(current_user.patient_profile.id)
        return render_template('dashboard.html', user=user_data, appointments=appointments)
    
    elif current_user.role == UserRole.DOCTOR and current_user.doctor_profile:
        from routes.appointments import get_doctor_appointments
        appointments = get_doctor_appointments(current_user.doctor_profile.id)
        return render_template('dashboard.html', user=user_data, appointments=appointments)
    
    return render_template('dashboard.html', user=user_data)

# API Routes
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }), 200

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if not all([username, email, password, role, first_name, last_name]):
        return jsonify({"error": "All fields are required"}), 400
    
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 400
    
    try:
        user_role = UserRole(role)
    except ValueError:
        return jsonify({"error": "Invalid role selected"}), 400
    
    # Create user
    user = User(
        username=username,
        email=email,
        role=user_role,
        first_name=first_name,
        last_name=last_name
    )
    user.set_password(password)
    db.session.add(user)
    
    # Create patient or doctor profile if needed
    if user_role == UserRole.PATIENT:
        patient = Patient(user=user)
        db.session.add(patient)
    elif user_role == UserRole.DOCTOR:
        doctor = Doctor(user=user, license_number='PENDING')
        db.session.add(doctor)
    
    db.session.commit()
    
    return jsonify({
        "message": "Registration successful",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }), 201

@auth_bp.route('/api/me')
@jwt_required()
def api_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value
    }), 200
