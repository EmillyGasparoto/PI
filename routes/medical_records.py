from flask import Blueprint, render_template, url_for, redirect, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, UserRole, Patient, Doctor, Appointment, MedicalRecord
from datetime import datetime

medical_records_bp = Blueprint('medical_records', __name__, url_prefix='/medical-records')

# Helper functions
def verify_medical_staff():
    if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        abort(403)

def verify_record_access(record_id):
    if not current_user.is_authenticated:
        abort(403)
    
    record = MedicalRecord.query.get_or_404(record_id)
    
    # If user is the patient
    if current_user.role == UserRole.PATIENT and current_user.patient_profile and current_user.patient_profile.id == record.patient_id:
        return record
    
    # If user is medical staff
    if current_user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        return record
    
    abort(403)

# Web Routes
@medical_records_bp.route('/')
@login_required
def list_records():
    # Filter records based on user role
    if current_user.role == UserRole.PATIENT and current_user.patient_profile:
        records = MedicalRecord.query.filter_by(patient_id=current_user.patient_profile.id).order_by(MedicalRecord.created_at.desc()).all()
        return render_template('medical_records/list.html', records=records, is_patient=True)
    
    elif current_user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        # For doctors, show records of their patients
        if current_user.role == UserRole.DOCTOR:
            # Get patients who have appointments with this doctor
            patient_ids = db.session.query(Appointment.patient_id).filter_by(doctor_id=current_user.doctor_profile.id).distinct().all()
            patient_ids = [pid[0] for pid in patient_ids]
            records = MedicalRecord.query.filter(MedicalRecord.patient_id.in_(patient_ids)).order_by(MedicalRecord.created_at.desc()).all()
        else:
            # Admins and staff can see all records
            records = MedicalRecord.query.order_by(MedicalRecord.created_at.desc()).all()
        
        return render_template('medical_records/list.html', records=records, is_medical_staff=True)
    
    flash('You do not have permission to view medical records.', 'danger')
    return redirect(url_for('auth.dashboard'))

@medical_records_bp.route('/<int:id>')
@login_required
def view_record(id):
    record = verify_record_access(id)
    return render_template('medical_records/view.html', record=record)

@medical_records_bp.route('/patient/<int:patient_id>')
@login_required
def patient_records(patient_id):
    # Verify access
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile or current_user.patient_profile.id != patient_id:
            flash('You can only view your own medical records.', 'danger')
            return redirect(url_for('auth.dashboard'))
    
    elif current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        flash('You do not have permission to view medical records.', 'danger')
        return redirect(url_for('auth.dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.created_at.desc()).all()
    
    return render_template('medical_records/patient_records.html', patient=patient, records=records)

@medical_records_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_record():
    verify_medical_staff()
    
    # Get all patients for the dropdown
    patients = Patient.query.join(User).all()
    
    # Get appointments for selection
    if current_user.role == UserRole.DOCTOR:
        appointments = Appointment.query.filter_by(doctor_id=current_user.doctor_profile.id, status='completed').all()
    else:
        appointments = Appointment.query.filter_by(status='completed').all()
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        appointment_id = request.form.get('appointment_id') or None
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        if not patient_id or not diagnosis:
            flash('Patient and diagnosis are required.', 'danger')
            return render_template('medical_records/create.html', patients=patients, appointments=appointments)
        
        try:
            record = MedicalRecord(
                patient_id=patient_id,
                appointment_id=appointment_id,
                diagnosis=diagnosis,
                treatment=treatment,
                prescription=prescription,
                notes=notes,
                created_by=current_user.id
            )
            db.session.add(record)
            db.session.commit()
            
            flash('Medical record created successfully.', 'success')
            return redirect(url_for('medical_records.view_record', id=record.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating medical record: {str(e)}', 'danger')
    
    return render_template('medical_records/create.html', patients=patients, appointments=appointments)

@medical_records_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_record(id):
    verify_medical_staff()
    
    record = MedicalRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        if not diagnosis:
            flash('Diagnosis is required.', 'danger')
            return render_template('medical_records/edit.html', record=record)
        
        try:
            record.diagnosis = diagnosis
            record.treatment = treatment
            record.prescription = prescription
            record.notes = notes
            
            db.session.commit()
            flash('Medical record updated successfully.', 'success')
            return redirect(url_for('medical_records.view_record', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating medical record: {str(e)}', 'danger')
    
    return render_template('medical_records/edit.html', record=record)

@medical_records_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_record(id):
    if current_user.role != UserRole.ADMIN:
        flash('Only administrators can delete medical records.', 'danger')
        return redirect(url_for('medical_records.list_records'))
    
    record = MedicalRecord.query.get_or_404(id)
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Medical record deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medical record: {str(e)}', 'danger')
    
    return redirect(url_for('medical_records.list_records'))

# API Routes
@medical_records_bp.route('/api/records')
@jwt_required()
def api_list_records():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Filter records based on user role
    if user.role == UserRole.PATIENT and user.patient_profile:
        records = MedicalRecord.query.filter_by(patient_id=user.patient_profile.id).order_by(MedicalRecord.created_at.desc()).all()
    
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        # Admins and staff can see all records
        records = MedicalRecord.query.order_by(MedicalRecord.created_at.desc()).all()
    
    elif user.role == UserRole.DOCTOR:
        # Get patients who have appointments with this doctor
        patient_ids = db.session.query(Appointment.patient_id).filter_by(doctor_id=user.doctor_profile.id).distinct().all()
        patient_ids = [pid[0] for pid in patient_ids]
        records = MedicalRecord.query.filter(MedicalRecord.patient_id.in_(patient_ids)).order_by(MedicalRecord.created_at.desc()).all()
    
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "patient_id": record.patient_id,
            "patient_name": record.patient.full_name,
            "appointment_id": record.appointment_id,
            "diagnosis": record.diagnosis,
            "treatment": record.treatment,
            "prescription": record.prescription,
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat()
        })
    
    return jsonify(result), 200

@medical_records_bp.route('/api/records/<int:id>')
@jwt_required()
def api_get_record(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    record = MedicalRecord.query.get_or_404(id)
    
    # Check if user has permission to view this record
    if user.role == UserRole.PATIENT and user.patient_profile and user.patient_profile.id == record.patient_id:
        pass  # Patient can view their own records
    elif user.role in [UserRole.ADMIN, UserRole.STAFF]:
        pass  # Admins and staff can view all records
    elif user.role == UserRole.DOCTOR:
        # Check if the patient has an appointment with this doctor
        has_appointment = Appointment.query.filter_by(
            doctor_id=user.doctor_profile.id,
            patient_id=record.patient_id
        ).first() is not None
        
        if not has_appointment:
            return jsonify({"error": "Unauthorized"}), 403
    else:
        return jsonify({"error": "Unauthorized"}), 403
    
    result = {
        "id": record.id,
        "patient_id": record.patient_id,
        "patient_name": record.patient.full_name,
        "appointment_id": record.appointment_id,
        "diagnosis": record.diagnosis,
        "treatment": record.treatment,
        "prescription": record.prescription,
        "notes": record.notes,
        "created_by": record.created_by,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat()
    }
    
    if record.created_by:
        creator = User.query.get(record.created_by)
        if creator:
            result["creator_name"] = f"{creator.first_name} {creator.last_name}"
    
    return jsonify(result), 200

@medical_records_bp.route('/api/patients/<int:patient_id>/records')
@jwt_required()
def api_patient_records(patient_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Check access permissions
    if user.role == UserRole.PATIENT:
        if not user.patient_profile or user.patient_profile.id != patient_id:
            return jsonify({"error": "Patients can only view their own medical records"}), 403
    
    elif user.role == UserRole.DOCTOR:
        # Check if the patient has an appointment with this doctor
        has_appointment = Appointment.query.filter_by(
            doctor_id=user.doctor_profile.id,
            patient_id=patient_id
        ).first() is not None
        
        if not has_appointment:
            return jsonify({"error": "Unauthorized"}), 403
    
    elif user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get patient records
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.created_at.desc()).all()
    
    result = []
    for record in records:
        record_data = {
            "id": record.id,
            "patient_id": record.patient_id,
            "appointment_id": record.appointment_id,
            "diagnosis": record.diagnosis,
            "treatment": record.treatment,
            "prescription": record.prescription,
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat()
        }
        
        if record.created_by:
            creator = User.query.get(record.created_by)
            if creator:
                record_data["creator_name"] = f"{creator.first_name} {creator.last_name}"
        
        result.append(record_data)
    
    return jsonify(result), 200

@medical_records_bp.route('/api/records', methods=['POST'])
@jwt_required()
def api_create_record():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        return jsonify({"error": "Only medical staff can create medical records"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Validate required fields
    if 'patient_id' not in data or 'diagnosis' not in data:
        return jsonify({"error": "Patient ID and diagnosis are required"}), 400
    
    # If doctor, verify the patient has an appointment with this doctor
    if user.role == UserRole.DOCTOR:
        has_appointment = Appointment.query.filter_by(
            doctor_id=user.doctor_profile.id,
            patient_id=data['patient_id']
        ).first() is not None
        
        if not has_appointment:
            return jsonify({"error": "You can only create records for your patients"}), 403
    
    try:
        record = MedicalRecord(
            patient_id=data['patient_id'],
            appointment_id=data.get('appointment_id'),
            diagnosis=data['diagnosis'],
            treatment=data.get('treatment'),
            prescription=data.get('prescription'),
            notes=data.get('notes'),
            created_by=user.id
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            "message": "Medical record created successfully",
            "record_id": record.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@medical_records_bp.route('/api/records/<int:id>', methods=['PUT'])
@jwt_required()
def api_update_record(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.STAFF]:
        return jsonify({"error": "Only medical staff can update medical records"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    record = MedicalRecord.query.get_or_404(id)
    
    # If doctor, verify the patient has an appointment with this doctor
    if user.role == UserRole.DOCTOR:
        has_appointment = Appointment.query.filter_by(
            doctor_id=user.doctor_profile.id,
            patient_id=record.patient_id
        ).first() is not None
        
        if not has_appointment:
            return jsonify({"error": "You can only update records for your patients"}), 403
    
    data = request.json
    
    try:
        if 'diagnosis' in data:
            record.diagnosis = data['diagnosis']
        if 'treatment' in data:
            record.treatment = data['treatment']
        if 'prescription' in data:
            record.prescription = data['prescription']
        if 'notes' in data:
            record.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            "message": "Medical record updated successfully",
            "record_id": record.id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@medical_records_bp.route('/api/records/<int:id>', methods=['DELETE'])
@jwt_required()
def api_delete_record(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        return jsonify({"error": "Only administrators can delete medical records"}), 403
    
    record = MedicalRecord.query.get_or_404(id)
    
    try:
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            "message": "Medical record deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
