from flask import Blueprint, render_template, url_for, redirect, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, UserRole, Patient, MedicalRecord
from datetime import datetime

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

# Helper functions
def verify_admin_or_doctor():
    if not current_user.is_authenticated or (current_user.role != UserRole.ADMIN and current_user.role != UserRole.DOCTOR):
        abort(403)

def verify_patient_or_medical_staff(patient_id):
    if not current_user.is_authenticated:
        abort(403)
    
    # If user is the patient
    if current_user.role == UserRole.PATIENT and current_user.patient_profile and current_user.patient_profile.id == patient_id:
        return True
    
    # If user is medical staff
    if current_user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        return True
    
    abort(403)

# Web Routes
@patients_bp.route('/')
@login_required
def list_patients():
    # Only admins, doctors, and staff can view all patients
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        flash('You do not have permission to access this resource.', 'danger')
        return redirect(url_for('auth.dashboard'))
    
    patients = Patient.query.join(User).all()
    return render_template('patients/list.html', patients=patients)

@patients_bp.route('/<int:id>')
@login_required
def view_patient(id):
    verify_patient_or_medical_staff(id)
    
    patient = Patient.query.get_or_404(id)
    return render_template('patients/view.html', patient=patient)

@patients_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_patient():
    verify_admin_or_doctor()
    
    if request.method == 'POST':
        # Get user data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get patient data
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        address = request.form.get('address')
        phone = request.form.get('phone')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        
        if not all([first_name, last_name, email, username, password, date_of_birth, gender]):
            flash('Required fields are missing.', 'danger')
            return render_template('patients/create.html')
        
        # Check if username or email already exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return render_template('patients/create.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.PATIENT
        )
        user.set_password(password)
        db.session.add(user)
        
        # Create patient profile
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            patient = Patient(
                user=user,
                date_of_birth=dob,
                gender=gender,
                blood_group=blood_group,
                address=address,
                phone=phone,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone
            )
            db.session.add(patient)
            db.session.commit()
            flash('Patient created successfully.', 'success')
            return redirect(url_for('patients.list_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating patient: {str(e)}', 'danger')
    
    return render_template('patients/create.html')

@patients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    verify_patient_or_medical_staff(id)
    
    patient = Patient.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get patient data
        patient.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else patient.date_of_birth
        patient.gender = request.form.get('gender') or patient.gender
        patient.blood_group = request.form.get('blood_group') or patient.blood_group
        patient.address = request.form.get('address') or patient.address
        patient.phone = request.form.get('phone') or patient.phone
        patient.emergency_contact_name = request.form.get('emergency_contact_name') or patient.emergency_contact_name
        patient.emergency_contact_phone = request.form.get('emergency_contact_phone') or patient.emergency_contact_phone
        
        # Get user data
        patient.user.first_name = request.form.get('first_name') or patient.user.first_name
        patient.user.last_name = request.form.get('last_name') or patient.user.last_name
        
        # Only admins can change email
        if current_user.role == UserRole.ADMIN:
            email = request.form.get('email')
            if email and email != patient.user.email:
                if User.query.filter_by(email=email).first():
                    flash('Email already exists.', 'danger')
                    return render_template('patients/edit.html', patient=patient)
                patient.user.email = email
        
        try:
            db.session.commit()
            flash('Patient updated successfully.', 'success')
            return redirect(url_for('patients.view_patient', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'danger')
    
    return render_template('patients/edit.html', patient=patient)

@patients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    if current_user.role != UserRole.ADMIN:
        flash('Only administrators can delete patients.', 'danger')
        return redirect(url_for('patients.list_patients'))
    
    patient = Patient.query.get_or_404(id)
    user = patient.user
    
    try:
        db.session.delete(patient)
        db.session.delete(user)
        db.session.commit()
        flash('Patient deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting patient: {str(e)}', 'danger')
    
    return redirect(url_for('patients.list_patients'))

# API Routes
@patients_bp.route('/api/patients')
@jwt_required()
def api_list_patients():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        return jsonify({"error": "Unauthorized"}), 403
    
    patients = Patient.query.join(User).all()
    result = []
    
    for patient in patients:
        result.append({
            "id": patient.id,
            "user_id": patient.user_id,
            "first_name": patient.user.first_name,
            "last_name": patient.user.last_name,
            "email": patient.user.email,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "phone": patient.phone,
            "full_name": patient.full_name
        })
    
    return jsonify(result), 200

@patients_bp.route('/api/patients/<int:id>')
@jwt_required()
def api_get_patient(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # If user is the patient
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == id:
        pass  # Allow access
    # If user is medical staff
    elif user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        pass  # Allow access
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    patient = Patient.query.get_or_404(id)
    
    result = {
        "id": patient.id,
        "user_id": patient.user_id,
        "first_name": patient.user.first_name,
        "last_name": patient.user.last_name,
        "email": patient.user.email,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "address": patient.address,
        "phone": patient.phone,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "full_name": patient.full_name
    }
    
    return jsonify(result), 200

@patients_bp.route('/api/patients', methods=['POST'])
@jwt_required()
def api_create_patient():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        return jsonify({"error": "Unauthorized"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'username', 'password', 'date_of_birth', 'gender']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if username or email already exists
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({"error": "Username or email already exists"}), 400
    
    try:
        # Create user
        new_user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole.PATIENT
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        
        # Create patient profile
        dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        patient = Patient(
            user=new_user,
            date_of_birth=dob,
            gender=data['gender'],
            blood_group=data.get('blood_group'),
            address=data.get('address'),
            phone=data.get('phone'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone')
        )
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            "message": "Patient created successfully",
            "patient_id": patient.id,
            "user_id": new_user.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@patients_bp.route('/api/patients/<int:id>', methods=['PUT'])
@jwt_required()
def api_update_patient(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # If user is the patient
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == id:
        pass  # Allow access
    # If user is medical staff
    elif user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        pass  # Allow access
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    patient = Patient.query.get_or_404(id)
    data = request.json
    
    try:
        # Update patient data
        if 'date_of_birth' in data:
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        if 'gender' in data:
            patient.gender = data['gender']
        if 'blood_group' in data:
            patient.blood_group = data['blood_group']
        if 'address' in data:
            patient.address = data['address']
        if 'phone' in data:
            patient.phone = data['phone']
        if 'emergency_contact_name' in data:
            patient.emergency_contact_name = data['emergency_contact_name']
        if 'emergency_contact_phone' in data:
            patient.emergency_contact_phone = data['emergency_contact_phone']
        
        # Update user data
        if 'first_name' in data:
            patient.user.first_name = data['first_name']
        if 'last_name' in data:
            patient.user.last_name = data['last_name']
        
        # Only admins can change email
        if 'email' in data and user.role == UserRole.ADMIN:
            if data['email'] != patient.user.email:
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({"error": "Email already exists"}), 400
                patient.user.email = data['email']
        
        db.session.commit()
        return jsonify({
            "message": "Patient updated successfully",
            "patient_id": patient.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@patients_bp.route('/api/patients/<int:id>', methods=['DELETE'])
@jwt_required()
def api_delete_patient(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "Only administrators can delete patients"}), 403
    
    patient = Patient.query.get_or_404(id)
    user_to_delete = patient.user
    
    try:
        db.session.delete(patient)
        db.session.delete(user_to_delete)
        db.session.commit()
        return jsonify({"message": "Patient deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
