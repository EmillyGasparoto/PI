from .auth import auth_bp
from .patients import patients_bp
from .doctors import doctors_bp
from .appointments import appointments_bp
from .medical_records import medical_records_bp

__all__ = ['auth_bp', 'patients_bp', 'doctors_bp', 'appointments_bp', 'medical_records_bp']