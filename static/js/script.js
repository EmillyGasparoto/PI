// Main script file for Clinic Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Alert auto close
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // Close after 5 seconds
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('table tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.indexOf(searchTerm) > -1) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Date picker initialization
    const datePickers = document.querySelectorAll('.datepicker');
    datePickers.forEach(function(picker) {
        picker.addEventListener('focus', function() {
            this.type = 'date';
        });
        picker.addEventListener('blur', function() {
            if (!this.value) {
                this.type = 'text';
            }
        });
    });

    // Password confirmation validation
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    
    if (passwordField && confirmPasswordField) {
        confirmPasswordField.addEventListener('input', function() {
            if (passwordField.value !== this.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Dynamic form elements based on user role
    const roleSelect = document.getElementById('role');
    const patientFields = document.getElementById('patientFields');
    const doctorFields = document.getElementById('doctorFields');
    
    if (roleSelect && (patientFields || doctorFields)) {
        roleSelect.addEventListener('change', function() {
            if (this.value === 'patient') {
                if (patientFields) patientFields.style.display = 'block';
                if (doctorFields) doctorFields.style.display = 'none';
            } else if (this.value === 'doctor') {
                if (patientFields) patientFields.style.display = 'none';
                if (doctorFields) doctorFields.style.display = 'block';
            } else {
                if (patientFields) patientFields.style.display = 'none';
                if (doctorFields) doctorFields.style.display = 'none';
            }
        });
    }

    // Print functionality
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Appointment status color change
    const statusElements = document.querySelectorAll('.appointment-status');
    statusElements.forEach(function(element) {
        const status = element.textContent.trim().toLowerCase();
        if (status === 'scheduled') {
            element.classList.add('badge', 'bg-info');
        } else if (status === 'completed') {
            element.classList.add('badge', 'bg-success');
        } else if (status === 'cancelled') {
            element.classList.add('badge', 'bg-danger');
        } else if (status === 'no_show') {
            element.classList.add('badge', 'bg-warning');
        }
    });
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

// Confirmation dialog
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}
