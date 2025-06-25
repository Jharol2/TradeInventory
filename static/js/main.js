// JavaScript principal para TradeInventory - Completamente Responsive

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

    // ===== FUNCIONALIDADES RESPONSIVE =====
    
    // Función para manejar el sidebar móvil
    function setupMobileSidebar() {
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        
        if (!mobileMenuToggle || !sidebar) return;
        
        // Función para abrir/cerrar sidebar
        function toggleSidebar() {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('show');
            document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
        }
        
        // Event listeners
        mobileMenuToggle.addEventListener('click', toggleSidebar);
        
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', toggleSidebar);
        }
        
        // Cerrar sidebar al hacer clic en un enlace (en móvil)
        const sidebarLinks = sidebar.querySelectorAll('.nav-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 575) {
                    toggleSidebar();
                }
            });
        });
        
        // Cerrar sidebar al redimensionar la ventana
        window.addEventListener('resize', function() {
            if (window.innerWidth > 575) {
                sidebar.classList.remove('show');
                sidebarOverlay.classList.remove('show');
                document.body.style.overflow = '';
            }
        });
    }
    
    // Función para hacer tablas responsivas
    function setupResponsiveTables() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            // Agregar clase table-responsive si no existe
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }
    
    // Función para ajustar formularios en móvil
    function setupResponsiveForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Agregar clases responsive a los campos
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (!input.classList.contains('form-control') && !input.classList.contains('form-select')) {
                    input.classList.add('form-control');
                }
            });
            
            // Hacer botones responsivos
            const buttons = form.querySelectorAll('.btn');
            buttons.forEach(button => {
                if (window.innerWidth <= 575) {
                    button.classList.add('w-100', 'mb-2');
                }
            });
        });
    }
    
    // Función para ajustar cards en móvil
    function setupResponsiveCards() {
        const cards = document.querySelectorAll('.card');
        
        cards.forEach(card => {
            if (window.innerWidth <= 575) {
                card.classList.add('mb-3');
            }
        });
    }
    
    // Función para detectar orientación del dispositivo
    function handleOrientationChange() {
        const isLandscape = window.innerWidth > window.innerHeight;
        
        if (isLandscape && window.innerWidth <= 575) {
            // Ajustes específicos para móvil en landscape
            document.body.classList.add('landscape-mobile');
        } else {
            document.body.classList.remove('landscape-mobile');
        }
    }
    
    // Función para optimizar imágenes en móvil
    function setupResponsiveImages() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            if (!img.classList.contains('img-fluid')) {
                img.classList.add('img-fluid');
            }
        });
    }
    
    // Función para ajustar modales en móvil
    function setupResponsiveModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            if (window.innerWidth <= 575) {
                modal.classList.add('modal-fullscreen-sm-down');
            }
        });
    }
    
    // Función para manejar gestos táctiles
    function setupTouchGestures() {
        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;
        
        document.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', function(e) {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Swipe horizontal para abrir/cerrar sidebar
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                const sidebar = document.getElementById('sidebar');
                if (sidebar && window.innerWidth <= 575) {
                    if (diffX > 0 && startX < 100) {
                        // Swipe izquierda desde el borde izquierdo
                        sidebar.classList.add('show');
                        document.getElementById('sidebarOverlay').classList.add('show');
                    } else if (diffX < 0 && sidebar.classList.contains('show')) {
                        // Swipe derecha para cerrar
                        sidebar.classList.remove('show');
                        document.getElementById('sidebarOverlay').classList.remove('show');
                    }
                }
            }
        });
    }
    
    // Función para optimizar rendimiento en móvil
    function setupMobileOptimizations() {
        if (window.innerWidth <= 575) {
            // Reducir animaciones en móvil
            document.body.style.setProperty('--transition-duration', '0.2s');
            
            // Optimizar scroll
            document.body.style.setProperty('scroll-behavior', 'smooth');
            
            // Prevenir zoom en inputs
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.style.fontSize = '16px'; // Previene zoom en iOS
            });
        }
    }
    
    // Función para manejar cambios de tamaño de ventana
    function handleResize() {
        setupResponsiveForms();
        setupResponsiveCards();
        setupResponsiveModals();
        setupMobileOptimizations();
        handleOrientationChange();
    }
    
    // Inicializar todas las funcionalidades responsive
    function initResponsiveFeatures() {
        setupMobileSidebar();
        setupResponsiveTables();
        setupResponsiveForms();
        setupResponsiveCards();
        setupResponsiveImages();
        setupResponsiveModals();
        setupTouchGestures();
        setupMobileOptimizations();
        handleOrientationChange();
        
        // Event listeners para cambios de tamaño
        window.addEventListener('resize', handleResize);
        window.addEventListener('orientationchange', handleOrientationChange);
    }
    
    // Ejecutar inicialización responsive
    initResponsiveFeatures();

    // ===== FUNCIONALIDADES EXISTENTES =====

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

        return {
            isValid: password.length >= minLength && hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar,
            errors: {
                length: password.length < minLength,
                upperCase: !hasUpperCase,
                lowerCase: !hasLowerCase,
                numbers: !hasNumbers,
                specialChar: !hasSpecialChar
            }
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
    window.debounce = function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
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
    // Prevenir envío de formularios con Enter en campos de búsqueda
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.type === 'search') {
            e.preventDefault();
            e.target.form.submit();
        }
    });

    // Mejorar accesibilidad
    document.addEventListener('keydown', function(e) {
        // Navegación con teclado para modales
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });

    // Lazy loading para imágenes
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Función para validar campos en tiempo real
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    
    // Remover clases de validación previas
    field.classList.remove('is-valid', 'is-invalid');
    
    // Validar campo requerido
    if (required && !value) {
        field.classList.add('is-invalid');
        return false;
    }
    
    // Validaciones específicas por tipo
    switch (type) {
        case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (value && !emailRegex.test(value)) {
                field.classList.add('is-invalid');
                return false;
            }
            break;
        case 'tel':
            const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
            if (value && !phoneRegex.test(value)) {
                field.classList.add('is-invalid');
                return false;
            }
            break;
        case 'number':
            if (value && isNaN(value)) {
                field.classList.add('is-invalid');
                return false;
            }
            break;
    }
    
    // Campo válido
    if (value) {
        field.classList.add('is-valid');
    }
    
    return true;
} 