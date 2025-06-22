"""
Configuración de URLs principales del sistema TradeInventory
Este módulo define todas las rutas URL del proyecto y cómo se mapean
a las vistas correspondientes.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .views import inicio, registro, perfil_usuario

def redirect_to_login(request):
    """
    Función de redirección para la URL raíz
    Redirige a los usuarios autenticados al dashboard y a los no autenticados al login
    
    Args:
        request: Objeto HttpRequest de Django
        
    Returns:
        HttpResponseRedirect: Redirige a 'home' o 'login' según el estado de autenticación
    """
    if request.user.is_authenticated:
        # Si el usuario ya está autenticado, redirigir al dashboard
        return redirect('home')
    else:
        # Si no está autenticado, redirigir al formulario de login
        return redirect('login')

# Configuración de todas las rutas URL del proyecto
urlpatterns = [
    # URL raíz - redirige según el estado de autenticación
    path('', redirect_to_login, name='root'),
    
    # Página de inicio/dashboard - solo para usuarios autenticados
    path('home/', inicio, name='home'),
    
    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # URLs de las aplicaciones del sistema
    # Cada include() carga las URLs específicas de cada aplicación
    path('productos/', include('productos.urls')),      # Gestión de productos
    path('categorias/', include('categorias.urls')),    # Gestión de categorías
    path('proveedores/', include('proveedores.urls')),  # Gestión de proveedores
    path('clientes/', include('clientes.urls')),        # Gestión de clientes
    path('almacenes/', include('almacenes.urls')),      # Gestión de almacenes
    path('ventas/', include('ventas.urls')),            # Gestión de ventas
    path('reportes/', include('reportes.urls')),        # Sistema de reportes
    
    # URLs de las APIs REST
    path('api/', include('tradeinventory.api_urls')),   # APIs REST
    
    # URLs del sistema de autenticación
    # Usa las vistas de autenticación de Django con plantillas personalizadas
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/registro/', registro, name='registro'),      # Registro personalizado
    path('accounts/perfil/', perfil_usuario, name='perfil'),    # Perfil personalizado
]

# Configuración para servir archivos de medios en desarrollo
# Solo se activa cuando DEBUG = True (modo desarrollo)
if settings.DEBUG:
    # Permite acceder a archivos subidos (imágenes, documentos) durante el desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 