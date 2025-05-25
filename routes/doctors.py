from flask import Blueprint, render_template, url_for, redirect, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, UserRole, Doctor, Specialization
from datetime import datetime
import json

doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

# Helper functions
def verify_admin():
    if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
        abort(403)

def verify_admin_or_self(doctor_id):
    if not current_user.is_authenticated:
        abort(403)
    
    # If user is the doctor
    if current_user.role == UserRole.DOCTOR and current_user.doctor_profile and current_user.doctor_profile.id == doctor_id:
        return True
    
    # If user is admin
    if current_user.role == UserRole.ADMIN:
        return True
    
    abort(403)

# Web Routes
@doctors_bp.route('/')
@login_required
def list_doctors():
    doctors = Doctor.query.join(User).all()
    specializations = Specialization.query.all()
    return render_template('doctors/list.html', doctors=doctors, specializations=specializations)

@doctors_bp.route('/<int:id>')
@login_required
def view_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    return render_template('doctors/view.html', doctor=doctor)

@doctors_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_doctor():
    verify_admin()
    
    specializations = Specialization.query.all()
    
    if request.method == 'POST':
        # Get user data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get doctor data
        specialization_id = request.form.get('specialization_id')
        license_number = request.form.get('license_number')
        experience_years = request.form.get('experience_years')
        consultation_fee = request.form.get('consultation_fee')
        availability = request.form.get('availability')
        
        if not all([first_name, last_name, email, username, password, license_number]):
            flash('Required fields are missing.', 'danger')
            return render_template('doctors/create.html', specializations=specializations)
        
        # Check if username or email already exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return render_template('doctors/create.html', specializations=specializations)
        
        # Check if license number is unique
        if Doctor.query.filter_by(license_number=license_number).first():
            flash('License number already exists.', 'danger')
            return render_template('doctors/create.html', specializations=specializations)
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.DOCTOR
        )
        user.set_password(password)
        db.session.add(user)
        
        # Create doctor profile
        try:
            doctor = Doctor(
                user=user,
                specialization_id=specialization_id,
                license_number=license_number,
                experience_years=int(experience_years) if experience_years else None,
                consultation_fee=float(consultation_fee) if consultation_fee else None,
                availability=availability
            )
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor created successfully.', 'success')
            return redirect(url_for('doctors.list_doctors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating doctor: {str(e)}', 'danger')
    
    return render_template('doctors/create.html', specializations=specializations)

@doctors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    verify_admin_or_self(id)
    
    doctor = Doctor.query.get_or_404(id)
    specializations = Specialization.query.all()
    
    if request.method == 'POST':
        # Get doctor data
        doctor.specialization_id = request.form.get('specialization_id') or doctor.specialization_id
        
        # Only admins can change license number
        if current_user.role == UserRole.ADMIN:
            license_number = request.form.get('license_number')
            if license_number and license_number != doctor.license_number:
                if Doctor.query.filter_by(license_number=license_number).first():
                    flash('License number already exists.', 'danger')
                    return render_template('doctors/edit.html', doctor=doctor, specializations=specializations)
                doctor.license_number = license_number
        
        doctor.experience_years = int(request.form.get('experience_years')) if request.form.get('experience_years') else doctor.experience_years
        doctor.consultation_fee = float(request.form.get('consultation_fee')) if request.form.get('consultation_fee') else doctor.consultation_fee
        doctor.availability = request.form.get('availability') or doctor.availability
        
        # Get user data
        doctor.user.first_name = request.form.get('first_name') or doctor.user.first_name
        doctor.user.last_name = request.form.get('last_name') or doctor.user.last_name
        
        # Only admins can change email
        if current_user.role == UserRole.ADMIN:
            email = request.form.get('email')
            if email and email != doctor.user.email:
                if User.query.filter_by(email=email).first():
                    flash('Email already exists.', 'danger')
                    return render_template('doctors/edit.html', doctor=doctor, specializations=specializations)
                doctor.user.email = email
        
        try:
            db.session.commit()
            flash('Doctor updated successfully.', 'success')
            return redirect(url_for('doctors.view_doctor', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating doctor: {str(e)}', 'danger')
    
    return render_template('doctors/edit.html', doctor=doctor, specializations=specializations)

@doctors_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_doctor(id):
    verify_admin()
    
    doctor = Doctor.query.get_or_404(id)
    user = doctor.user
    
    try:
        db.session.delete(doctor)
        db.session.delete(user)
        db.session.commit()
        flash('Doctor deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting doctor: {str(e)}', 'danger')
    
    return redirect(url_for('doctors.list_doctors'))

@doctors_bp.route('/specializations')
@login_required
def list_specializations():
    verify_admin()
    
    specializations = Specialization.query.all()
    return render_template('doctors/specializations.html', specializations=specializations)

@doctors_bp.route('/specializations/create', methods=['GET', 'POST'])
@login_required
def create_specialization():
    verify_admin()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Name is required.', 'danger')
            return render_template('doctors/create_specialization.html')
        
        if Specialization.query.filter_by(name=name).first():
            flash('Specialization already exists.', 'danger')
            return render_template('doctors/create_specialization.html')
        
        try:
            specialization = Specialization(name=name, description=description)
            db.session.add(specialization)
            db.session.commit()
            flash('Specialization created successfully.', 'success')
            return redirect(url_for('doctors.list_specializations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating specialization: {str(e)}', 'danger')
    
    return render_template('doctors/create_specialization.html')

# API Routes
@doctors_bp.route('/api/doctors')
@jwt_required()
def api_list_doctors():
    doctors = Doctor.query.join(User).all()
    result = []
    
    for doctor in doctors:
        result.append({
            "id": doctor.id,
            "user_id": doctor.user_id,
            "first_name": doctor.user.first_name,
            "last_name": doctor.user.last_name,
            "email": doctor.user.email,
            "specialization_id": doctor.specialization_id,
            "specialization_name": doctor.specialization.name if doctor.specialization else None,
            "license_number": doctor.license_number,
            "experience_years": doctor.experience_years,
            "consultation_fee": doctor.consultation_fee,
            "availability": doctor.availability,
            "full_name": doctor.full_name
        })
    
    return jsonify(result), 200

@doctors_bp.route('/api/doctors/<int:id>')
@jwt_required()
def api_get_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    
    result = {
        "id": doctor.id,
        "user_id": doctor.user_id,
        "first_name": doctor.user.first_name,
        "last_name": doctor.user.last_name,
        "email": doctor.user.email,
        "specialization_id": doctor.specialization_id,
        "specialization_name": doctor.specialization.name if doctor.specialization else None,
        "license_number": doctor.license_number,
        "experience_years": doctor.experience_years,
        "consultation_fee": doctor.consultation_fee,
        "availability": doctor.availability,
        "full_name": doctor.full_name
    }
    
    return jsonify(result), 200

@doctors_bp.route('/api/doctors', methods=['POST'])
@jwt_required()
def api_create_doctor():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "Only administrators can create doctors"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'username', 'password', 'license_number']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if username or email already exists
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({"error": "Username or email already exists"}), 400
    
    # Check if license number is unique
    if Doctor.query.filter_by(license_number=data['license_number']).first():
        return jsonify({"error": "License number already exists"}), 400
    
    try:
        # Create user
        new_user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole.DOCTOR
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        
        # Create doctor profile
        doctor = Doctor(
            user=new_user,
            specialization_id=data.get('specialization_id'),
            license_number=data['license_number'],
            experience_years=data.get('experience_years'),
            consultation_fee=data.get('consultation_fee'),
            availability=data.get('availability')
        )
        db.session.add(doctor)
        db.session.commit()
        
        return jsonify({
            "message": "Doctor created successfully",
            "doctor_id": doctor.id,
            "user_id": new_user.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@doctors_bp.route('/api/doctors/<int:id>', methods=['PUT'])
@jwt_required()
def api_update_doctor(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # If user is the doctor
    is_self = user.role == UserRole.DOCTOR and user.doctor_profile and user.doctor_profile.id == id
    # If user is admin
    is_admin = user.role == UserRole.ADMIN
    
    if not (is_self or is_admin):
        return jsonify({"error": "Unauthorized"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    doctor = Doctor.query.get_or_404(id)
    data = request.json
    
    try:
        # Update doctor data
        if 'specialization_id' in data:
            doctor.specialization_id = data['specialization_id']
        
        # Only admins can change license number
        if 'license_number' in data and is_admin:
            if data['license_number'] != doctor.license_number:
                if Doctor.query.filter_by(license_number=data['license_number']).first():
                    return jsonify({"error": "License number already exists"}), 400
                doctor.license_number = data['license_number']
        
        if 'experience_years' in data:
            doctor.experience_years = data['experience_years']
        if 'consultation_fee' in data:
            doctor.consultation_fee = data['consultation_fee']
        if 'availability' in data:
            doctor.availability = data['availability']
        
        # Update user data
        if 'first_name' in data:
            doctor.user.first_name = data['first_name']
        if 'last_name' in data:
            doctor.user.last_name = data['last_name']
        
        # Only admins can change email
        if 'email' in data and is_admin:
            if data['email'] != doctor.user.email:
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({"error": "Email already exists"}), 400
                doctor.user.email = data['email']
        
        db.session.commit()
        return jsonify({
            "message": "Doctor updated successfully",
            "doctor_id": doctor.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@doctors_bp.route('/api/doctors/<int:id>', methods=['DELETE'])
@jwt_required()
def api_delete_doctor(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "Only administrators can delete doctors"}), 403
    
    doctor = Doctor.query.get_or_404(id)
    user_to_delete = doctor.user
    
    try:
        db.session.delete(doctor)
        db.session.delete(user_to_delete)
        db.session.commit()
        return jsonify({"message": "Doctor deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@doctors_bp.route('/api/specializations')
@jwt_required()
def api_list_specializations():
    specializations = Specialization.query.all()
    result = []
    
    for specialization in specializations:
        result.append({
            "id": specialization.id,
            "name": specialization.name,
            "description": specialization.description
        })
    
    return jsonify(result), 200

@doctors_bp.route('/api/specializations', methods=['POST'])
@jwt_required()
def api_create_specialization():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "Only administrators can create specializations"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    if 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    if Specialization.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Specialization already exists"}), 400
    
    try:
        specialization = Specialization(
            name=data['name'],
            description=data.get('description')
        )
        db.session.add(specialization)
        db.session.commit()
        
        return jsonify({
            "message": "Specialization created successfully",
            "specialization_id": specialization.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
        from flask import Blueprint, render_template

from flask_login import login_required
from models import User
from sqlalchemy import and_

doctors = User.query.filter(User.role == "doctor").all()

@doctors_bp.route('/')
def listar_medicos():
    doctors = [
        {'id': 1, 'name': 'Dra. Ana Lima'},
        {'id': 2, 'name': 'Dr. João Mendes'},
        {'id': 3, 'name': 'Dra. Camila Rocha'},
    ]
    return render_template('medicos.html', doctors=doctors)

@doctors_bp.route('/available')
@login_required
def listar_medicos_disponiveis():
    doctors = User.query.filter(
        and_(
            User.role == "doctor",
            User.is_active == True
        )
    ).all()
    return render_template('medicos_disponiveis.html', doctors=doctors)
