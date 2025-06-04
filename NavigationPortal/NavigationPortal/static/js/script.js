// General utility functions and event handlers

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Flash message auto-dismiss
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            if (bootstrap && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 5000);
    
    // Custom form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Password field toggle for credential forms
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const passwordField = document.querySelector(this.getAttribute('data-target'));
            if (passwordField) {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle icon
                this.querySelector('i').classList.toggle('fa-eye');
                this.querySelector('i').classList.toggle('fa-eye-slash');
            }
        });
    });
    
    // Form input masking for sensitive data
    const maskFields = document.querySelectorAll('[data-mask]');
    maskFields.forEach(function(field) {
        field.addEventListener('focus', function() {
            // Unmask on focus if needed
        });
        
        field.addEventListener('blur', function() {
            // Re-mask on blur if needed
        });
    });
});

// Confirmation dialog helper
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Date range validation for download scheduling
function validateDateRange(startId, endId, errorId) {
    const startDate = document.getElementById(startId).value;
    const endDate = document.getElementById(endId).value;
    const errorElement = document.getElementById(errorId);
    
    if (startDate && endDate) {
        if (new Date(startDate) > new Date(endDate)) {
            errorElement.textContent = 'Start date must be before end date';
            errorElement.style.display = 'block';
            return false;
        } else {
            errorElement.style.display = 'none';
            return true;
        }
    }
    return true;
}
