from flask import Blueprint, render_template, url_for, redirect, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, UserRole, Patient, Doctor, Appointment, AppointmentStatus
from datetime import datetime, date, time

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

# Helper functions
def verify_appointment_access(appointment_id):
    if not current_user.is_authenticated:
        abort(403)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # If user is the patient
    if current_user.role == UserRole.PATIENT and current_user.patient_profile and current_user.patient_profile.id == appointment.patient_id:
        return appointment
    
    # If user is the doctor
    if current_user.role == UserRole.DOCTOR and current_user.doctor_profile and current_user.doctor_profile.id == appointment.doctor_id:
        return appointment
    
    # If user is admin or staff
    if current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
        return appointment
    
    abort(403)

def get_patient_appointments(patient_id):
    return Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

def get_doctor_appointments(doctor_id):
    return Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

# Web Routes
@appointments_bp.route('/')
@login_required
def list_appointments():
    # Filter appointments based on user role
    if current_user.role == UserRole.PATIENT and current_user.patient_profile:
        appointments = get_patient_appointments(current_user.patient_profile.id)
        return render_template('appointments/list.html', appointments=appointments, is_patient=True)
    
    elif current_user.role == UserRole.DOCTOR and current_user.doctor_profile:
        appointments = get_doctor_appointments(current_user.doctor_profile.id)
        return render_template('appointments/list.html', appointments=appointments, is_doctor=True)
    
    elif current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
        # Admins and staff can see all appointments
        appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
        return render_template('appointments/list.html', appointments=appointments, is_admin=True)
    
    flash('You do not have permission to view appointments.', 'danger')
    return redirect(url_for('auth.dashboard'))

@appointments_bp.route('/<int:id>')
@login_required
def view_appointment(id):
    appointment = verify_appointment_access(id)
    return render_template('appointments/view.html', appointment=appointment)

@appointments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_appointment():
    # Get all doctors for the dropdown
    doctors = Doctor.query.join(User).all()
    
    # For staff or admin, get all patients for the dropdown
    if current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
        patients = Patient.query.join(User).all()
    else:
        patients = None
    
    if request.method == 'POST':
        # Get appointment data
        doctor_id = request.form.get('doctor_id')
        
        # Determine patient_id based on the role
        if current_user.role == UserRole.PATIENT:
            patient_id = current_user.patient_profile.id
        else:
            patient_id = request.form.get('patient_id')
        
        appointment_date_str = request.form.get('appointment_date')
        appointment_time_str = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        if not all([doctor_id, patient_id, appointment_date_str, appointment_time_str]):
            flash('Required fields are missing.', 'danger')
            return render_template('appointments/create.html', doctors=doctors, patients=patients)
        
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            # Check if appointment date is in the past
            if appointment_date < date.today():
                flash('Appointment date cannot be in the past.', 'danger')
                return render_template('appointments/create.html', doctors=doctors, patients=patients)
            
            # Create appointment
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                reason=reason,
                status=AppointmentStatus.SCHEDULED
            )
            db.session.add(appointment)
            db.session.commit()
            
            flash('Appointment created successfully.', 'success')
            return redirect(url_for('appointments.list_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'danger')
    
    return render_template('appointments/create.html', doctors=doctors, patients=patients)

@appointments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    appointment = verify_appointment_access(id)
    
    # Get all doctors for the dropdown
    doctors = Doctor.query.join(User).all()
    
    # For staff or admin, get all patients for the dropdown
    if current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
        patients = Patient.query.join(User).all()
    else:
        patients = None
    
    if request.method == 'POST':
        # Get appointment data
        if current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
            appointment.doctor_id = request.form.get('doctor_id') or appointment.doctor_id
            appointment.patient_id = request.form.get('patient_id') or appointment.patient_id
        
        appointment_date_str = request.form.get('appointment_date')
        appointment_time_str = request.form.get('appointment_time')
        reason = request.form.get('reason')
        status_str = request.form.get('status')
        notes = request.form.get('notes')
        
        try:
            if appointment_date_str:
                appointment.appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            
            if appointment_time_str:
                appointment.appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            if reason:
                appointment.reason = reason
            
            if status_str:
                appointment.status = AppointmentStatus(status_str)
            
            if notes:
                appointment.notes = notes
            
            db.session.commit()
            flash('Appointment updated successfully.', 'success')
            return redirect(url_for('appointments.view_appointment', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating appointment: {str(e)}', 'danger')
    
    return render_template('appointments/edit.html', appointment=appointment, doctors=doctors, patients=patients)

@appointments_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    appointment = verify_appointment_access(id)
    
    if appointment.status != AppointmentStatus.SCHEDULED:
        flash('Only scheduled appointments can be cancelled.', 'danger')
        return redirect(url_for('appointments.view_appointment', id=id))
    
    try:
        appointment.status = AppointmentStatus.CANCELLED
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
    
    return redirect(url_for('appointments.view_appointment', id=id))

@appointments_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete_appointment(id):
    appointment = verify_appointment_access(id)
    
    # Only doctors, admins, and staff can mark appointments as completed
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN, UserRole.STAFF]:
        flash('You do not have permission to complete appointments.', 'danger')
        return redirect(url_for('appointments.view_appointment', id=id))
    
    if appointment.status != AppointmentStatus.SCHEDULED:
        flash('Only scheduled appointments can be completed.', 'danger')
        return redirect(url_for('appointments.view_appointment', id=id))
    
    try:
        appointment.status = AppointmentStatus.COMPLETED
        db.session.commit()
        flash('Appointment marked as completed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing appointment: {str(e)}', 'danger')
    
    return redirect(url_for('appointments.view_appointment', id=id))

# API Routes
@appointments_bp.route('/api/appointments')
@jwt_required()
def api_list_appointments():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Filter appointments based on user role
    if user.role == UserRole.PATIENT and user.patient_profile:
        appointments = Appointment.query.filter_by(patient_id=user.patient_profile.id).all()
    
    elif user.role == UserRole.DOCTOR and user.doctor_profile:
        appointments = Appointment.query.filter_by(doctor_id=user.doctor_profile.id).all()
    
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        # Admins and staff can see all appointments
        appointments = Appointment.query.all()
    
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    result = []
    for appointment in appointments:
        result.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient.full_name,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor.full_name,
            "appointment_date": appointment.appointment_date.isoformat(),
            "appointment_time": appointment.appointment_time.isoformat(),
            "reason": appointment.reason,
            "status": appointment.status.value,
            "notes": appointment.notes,
            "created_at": appointment.created_at.isoformat()
        })
    
    return jsonify(result), 200

@appointments_bp.route('/api/appointments/<int:id>')
@jwt_required()
def api_get_appointment(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    appointment = Appointment.query.get_or_404(id)
    
    # Check if user has permission to view this appointment
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == appointment.patient_id:
        pass  # Patient can view their own appointments
    elif user.role == UserRole.DOCTOR and user.doctor_profile and user.doctor_profile.id == appointment.doctor_id:
        pass  # Doctor can view appointments where they are the doctor
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        pass  # Admins and staff can view all appointments
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    result = {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.full_name,
        "doctor_id": appointment.doctor_id,
        "doctor_name": appointment.doctor.full_name,
        "appointment_date": appointment.appointment_date.isoformat(),
        "appointment_time": appointment.appointment_time.isoformat(),
        "reason": appointment.reason,
        "status": appointment.status.value,
        "notes": appointment.notes,
        "created_at": appointment.created_at.isoformat(),
        "updated_at": appointment.updated_at.isoformat()
    }
    
    return jsonify(result), 200

@appointments_bp.route('/api/appointments', methods=['POST'])
@jwt_required()
def api_create_appointment():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Determine patient_id based on the role
    if user.role == UserRole.PATIENT and user.patient_profile:
        patient_id = user.patient_profile.id
    else:
        patient_id = data.get('patient_id')
    
    doctor_id = data.get('doctor_id')
    appointment_date_str = data.get('appointment_date')
    appointment_time_str = data.get('appointment_time')
    reason = data.get('reason')
    
    if not all([patient_id, doctor_id, appointment_date_str, appointment_time_str]):
        return jsonify({"error": "Required fields missing"}), 400
    
    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        
        # Check if appointment date is in the past
        if appointment_date < date.today():
            return jsonify({"error": "Appointment date cannot be in the past"}), 400
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status=AppointmentStatus.SCHEDULED
        )
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            "message": "Appointment created successfully",
            "appointment_id": appointment.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@appointments_bp.route('/api/appointments/<int:id>', methods=['PUT'])
@jwt_required()
def api_update_appointment(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    appointment = Appointment.query.get_or_404(id)
    
    # Check if user has permission to update this appointment
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == appointment.patient_id:
        pass  # Patient can update their own appointments
    elif user.role == UserRole.DOCTOR and user.doctor_profile and user.doctor_profile.id == appointment.doctor_id:
        pass  # Doctor can update appointments where they are the doctor
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        pass  # Admins and staff can update all appointments
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    try:
        # Update appointment data based on user role
        if user.role in [UserRole.ADMIN, UserRole.STAFF]:
            if 'doctor_id' in data:
                appointment.doctor_id = data['doctor_id']
            if 'patient_id' in data:
                appointment.patient_id = data['patient_id']
        
        if 'appointment_date' in data:
            appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        
        if 'appointment_time' in data:
            appointment.appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        
        if 'reason' in data:
            appointment.reason = data['reason']
        
        if 'status' in data:
            # Validate status changes based on role
            new_status = AppointmentStatus(data['status'])
            current_status = appointment.status
            
            # Patients can only cancel their appointments
            if user.role == UserRole.PATIENT and new_status != AppointmentStatus.CANCELLED:
                return jsonify({"error": "Patients can only cancel appointments"}), 403
            
            # Only scheduled appointments can be updated
            if current_status != AppointmentStatus.SCHEDULED and user.role != UserRole.ADMIN:
                return jsonify({"error": "Only scheduled appointments can be updated"}), 400
            
            appointment.status = new_status
        
        if 'notes' in data:
            # Only medical staff can add notes
            if user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
                return jsonify({"error": "Only medical staff can add notes"}), 403
            appointment.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            "message": "Appointment updated successfully",
            "appointment_id": appointment.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@appointments_bp.route('/api/appointments/<int:id>/cancel', methods=['POST'])
@jwt_required()
def api_cancel_appointment(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    appointment = Appointment.query.get_or_404(id)
    
    # Check if user has permission to cancel this appointment
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == appointment.patient_id:
        pass  # Patient can cancel their own appointments
    elif user.role == UserRole.DOCTOR and user.doctor_profile and user.doctor_profile.id == appointment.doctor_id:
        pass  # Doctor can cancel appointments where they are the doctor
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        pass  # Admins and staff can cancel all appointments
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    if appointment.status != AppointmentStatus.SCHEDULED:
        return jsonify({"error": "Only scheduled appointments can be cancelled"}), 400
    
    try:
        appointment.status = AppointmentStatus.CANCELLED
        db.session.commit()
        
        return jsonify({
            "message": "Appointment cancelled successfully",
            "appointment_id": appointment.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@appointments_bp.route('/api/appointments/<int:id>/complete', methods=['POST'])
@jwt_required()
def api_complete_appointment(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.DOCTOR, UserRole.ADMIN, UserRole.STAFF]:
        return jsonify({"error": "Only medical staff can complete appointments"}), 403
    
    appointment = Appointment.query.get_or_404(id)
    
    # Doctors can only complete their own appointments
    if user.role == UserRole.DOCTOR and user.doctor_profile.id != appointment.doctor_id:
        return jsonify({"error": "Doctors can only complete their own appointments"}), 403
    
    if appointment.status != AppointmentStatus.SCHEDULED:
        return jsonify({"error": "Only scheduled appointments can be completed"}), 400
    
    try:
        appointment.status = AppointmentStatus.COMPLETED
        db.session.commit()
        
        return jsonify({
            "message": "Appointment marked as completed",
            "appointment_id": appointment.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
