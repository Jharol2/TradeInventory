from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import RegistroUsuarioForm, CambioPasswordForm
from productos.models import Producto
from ventas.models import Venta
from clientes.models import Cliente

def inicio(request):
    # Obtener estadísticas básicas
    total_productos = Producto.objects.count()
    total_ventas = Venta.objects.count()
    total_clientes = Cliente.objects.count()
    
    # Obtener productos con stock bajo
    productos_bajo_stock = Producto.objects.filter(stock_actual__lte=5)[:5]
    
    # Obtener últimas ventas
    ultimas_ventas = Venta.objects.all().order_by('-fecha')[:5]
    
    context = {
        'total_productos': total_productos,
        'total_ventas': total_ventas,
        'total_clientes': total_clientes,
        'productos_bajo_stock': productos_bajo_stock,
        'ultimas_ventas': ultimas_ventas,
    }
    
    return render(request, 'inicio.html', context)

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Autenticar al usuario después del registro
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'¡Bienvenido {username}! Tu cuenta ha sido creada exitosamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})

@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        form = CambioPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Actualizar la sesión para evitar que el usuario tenga que volver a iniciar sesión
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CambioPasswordForm(request.user)
    
    return render(request, 'registration/perfil.html', {'form': form}) 