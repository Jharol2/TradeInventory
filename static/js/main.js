// JavaScript principal para TradeInventory

document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Función para mostrar mensajes de confirmación
    // window.showConfirmModal = function(url, message, buttonText = 'Confirmar') {
    //     const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    //     document.getElementById('confirmModalMessage').textContent = message;
    //     document.getElementById('confirmModalButton').textContent = buttonText;
    //     document.getElementById('confirmModalButton').href = url;
    //     modal.show();
    // };

    // Función para mostrar loading en botones
    window.showLoading = function(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="loading"></span> Procesando...';
        button.disabled = true;
        return originalText;
    };

    window.hideLoading = function(button, originalText) {
        button.innerHTML = originalText;
        button.disabled = false;
    };

    // Función para validar formularios
    window.validateForm = function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        return isValid;
    };

    // Función para formatear números como moneda
    window.formatCurrency = function(amount) {
        return new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN'
        }).format(amount);
    };

    // Función para formatear fechas
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-MX', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    // Función para mostrar notificaciones
    window.showNotification = function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.messages') || document.body;
        container.appendChild(alertDiv);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    };

    // Función para hacer búsquedas en tiempo real
    window.setupLiveSearch = function(inputSelector, tableSelector) {
        const searchInput = document.querySelector(inputSelector);
        const table = document.querySelector(tableSelector);
        
        if (!searchInput || !table) return;

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    };

    // Función para exportar tablas a CSV
    window.exportTableToCSV = function(tableSelector, filename = 'export.csv') {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = [];
            
            cols.forEach(col => {
                rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
            });
            
            csv.push(rowData.join(','));
        });

        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    // Función para imprimir elementos
    window.printElement = function(elementSelector) {
        const element = document.querySelector(elementSelector);
        if (!element) return;

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Imprimir</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; }
                        @media print {
                            .no-print { display: none !important; }
                        }
                    </style>
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    };

    // Función para copiar al portapapeles
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Texto copiado al portapapeles', 'success');
            }).catch(() => {
                showNotification('Error al copiar texto', 'danger');
            });
        } else {
            // Fallback para navegadores más antiguos
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification('Texto copiado al portapapeles', 'success');
        }
    };

    // Función para validar contraseñas
    window.validatePassword = function(password) {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        const errors = [];
        if (password.length < minLength) {
            errors.push(`La contraseña debe tener al menos ${minLength} caracteres`);
        }
        if (!hasUpperCase) {
            errors.push('La contraseña debe contener al menos una letra mayúscula');
        }
        if (!hasLowerCase) {
            errors.push('La contraseña debe contener al menos una letra minúscula');
        }
        if (!hasNumbers) {
            errors.push('La contraseña debe contener al menos un número');
        }
        if (!hasSpecialChar) {
            errors.push('La contraseña debe contener al menos un carácter especial');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    };

    // Función para mostrar/ocultar contraseñas
    window.togglePasswordVisibility = function(inputId) {
        const input = document.getElementById(inputId);
        const icon = document.querySelector(`[data-toggle-password="${inputId}"]`);
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    // Función para validar emails
    window.validateEmail = function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    // Función para formatear números de teléfono
    window.formatPhoneNumber = function(phone) {
        const cleaned = phone.replace(/\D/g, '');
        const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
        if (match) {
            return '(' + match[1] + ') ' + match[2] + '-' + match[3];
        }
        return phone;
    };

    // Función para generar IDs únicos
    window.generateUniqueId = function() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    };

    // Función para debounce
    window.debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // Función para throttle
    window.throttle = function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };

    // Configurar eventos globales
    setupGlobalEvents();
});

// Función para configurar eventos globales
function setupGlobalEvents() {
    // Auto-hide alerts después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Validación de formularios en tiempo real
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });

    // Configurar tooltips para elementos dinámicos
    document.addEventListener('mouseover', function(e) {
        if (e.target.hasAttribute('data-bs-toggle') && e.target.getAttribute('data-bs-toggle') === 'tooltip') {
            if (!e.target.hasAttribute('data-bs-original-title')) {
                new bootstrap.Tooltip(e.target);
            }
        }
    });
}

// Función para validar campos individuales
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');

    // Limpiar clases de validación previas
    field.classList.remove('is-valid', 'is-invalid');

    // Validar campo requerido
    if (required && !value) {
        field.classList.add('is-invalid');
        return false;
    }

    // Validaciones específicas por tipo
    if (value) {
        switch (type) {
            case 'email':
                if (!window.validateEmail(value)) {
                    field.classList.add('is-invalid');
                    return false;
                }
                break;
            case 'tel':
                if (value.length < 10) {
                    field.classList.add('is-invalid');
                    return false;
                }
                break;
            case 'number':
                if (isNaN(value) || value < 0) {
                    field.classList.add('is-invalid');
                    return false;
                }
                break;
        }
    }

    // Si pasa todas las validaciones
    if (value) {
        field.classList.add('is-valid');
    }
    return true;
} 