"""
Sistema de Gestión de Ventas para TradeInventory
Este módulo maneja todas las operaciones relacionadas con ventas:

Funcionalidades principales:
- Listado de ventas del día
- Creación de nuevas ventas
- Gestión de ventas a fiado
- Control de stock automático
- Detalles de ventas
- Historial completo de ventas

Características:
- Transacciones atómicas para consistencia
- Control de stock en tiempo real
- Soporte para ventas a fiado
- Validaciones de stock
- Cálculo automático de totales
- Interfaz AJAX para ventas dinámicas
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from .models import Venta, DetalleVenta
from productos.models import Producto
from clientes.models import Cliente, Fiado, DetalleFiado
from categorias.models import Categoria
import json

@login_required
def lista_ventas(request):
    """
    Vista principal para mostrar ventas del día y preparar nueva venta
    Muestra estadísticas del día y datos necesarios para crear ventas
    
    Args:
        request: Objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza la página de ventas con datos del día
        
    Funcionalidades:
        - Muestra ventas del día actual
        - Calcula total de ventas del día
        - Proporciona datos para nueva venta (productos, categorías, clientes)
        - Interfaz para iniciar nueva venta
    """
    # Obtener ventas del día actual
    hoy = timezone.now().date()
    ventas_dia = Venta.objects.filter(fecha__date=hoy)
    
    # Calcular total de ventas del día
    total_ventas_dia = ventas_dia.aggregate(total=Sum('total'))['total'] or 0

    # Obtener datos necesarios para la vista de venta
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    clientes = Cliente.objects.all()

    # Preparar contexto para la plantilla
    context = {
        'ventas_dia': ventas_dia,
        'total_ventas_dia': total_ventas_dia,
        'productos': productos,
        'categorias': categorias,
        'clientes': clientes,
    }
    return render(request, 'ventas/lista_ventas.html', context)

@login_required
def nueva_venta(request):
    """
    Vista para crear una nueva venta
    Maneja la creación de ventas con control de stock y transacciones
    
    Args:
        request: Objeto HttpRequest con datos JSON en el body:
            - cliente_id: ID del cliente (opcional)
            - es_fiado: Boolean indicando si es venta a fiado
            - productos: Lista de productos con cantidad
            
    Returns:
        JsonResponse: Resultado de la operación (éxito/error)
        
    Funcionalidades:
        - Validación de stock en tiempo real
        - Transacciones atómicas para consistencia
        - Actualización automática de stock
        - Cálculo automático de totales
        - Soporte para ventas a fiado
        - Bloqueo de registros durante actualización
    """
    if request.method == 'POST':
        try:
            # Parsear datos JSON del request
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            es_fiado = data.get('es_fiado', False)
            productos_data = data.get('productos', [])

            # Validar que hay productos en la venta
            if not productos_data:
                return JsonResponse({'success': False, 'error': 'No hay productos en la venta'})

            # Usar transacción para asegurar consistencia de datos
            # Si algo falla, se revierten todos los cambios
            with transaction.atomic():
                # Crear la venta inicial con total 0
                venta = Venta.objects.create(
                    cliente_id=cliente_id if cliente_id else None,
                    es_fiado=es_fiado,
                    total=0  # Se actualizará después de procesar productos
                )

                total_venta = 0
                # Procesar cada producto en la venta
                for producto_data in productos_data:
                    # Usar select_for_update para bloquear el registro durante la actualización
                    # Esto evita problemas de concurrencia
                    producto = Producto.objects.select_for_update().get(id=producto_data['id'])
                    cantidad = producto_data['cantidad']
                    precio = producto.precio
                    subtotal = precio * cantidad

                    # Verificar que hay suficiente stock
                    if producto.stock_actual < cantidad:
                        raise Exception(f'Stock insuficiente para {producto.nombre}')

                    # Crear detalle de venta
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal
                    )

                    # Actualizar stock del producto
                    producto.stock_actual -= cantidad
                    producto.save()

                    # Acumular total de la venta
                    total_venta += subtotal

                # Actualizar total de la venta
                venta.total = total_venta
                venta.save()

                # Retornar éxito con ID de la venta creada
                return JsonResponse({'success': True, 'venta_id': venta.id})

        except Exception as e:
            # Retornar error si algo falla
            return JsonResponse({'success': False, 'error': str(e)})

    # Si no es POST, retornar error
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def detalle_venta(request, pk):
    """
    Vista para mostrar detalles de una venta específica
    Muestra información completa de la venta y sus productos
    
    Args:
        request: Objeto HttpRequest
        pk: ID de la venta a mostrar
        
    Returns:
        HttpResponse: Renderiza el detalle de la venta
        
    Funcionalidades:
        - Muestra información de la venta
        - Lista todos los productos vendidos
        - Muestra cantidades y precios
        - Información del cliente (si aplica)
    """
    # Obtener la venta específica o mostrar error 404
    venta = get_object_or_404(Venta, id=pk)
    
    # Obtener todos los detalles de la venta
    detalles = DetalleVenta.objects.filter(venta=venta)
    
    # Preparar contexto para la plantilla
    context = {
        'venta': venta,
        'detalles': detalles,
    }
    return render(request, 'ventas/detalle_venta.html', context)

@login_required
def historial_ventas(request):
    """
    Vista para mostrar historial completo de ventas
    Lista todas las ventas ordenadas por fecha
    
    Args:
        request: Objeto HttpRequest
        
    Returns:
        HttpResponse: Renderiza el historial de ventas
        
    Funcionalidades:
        - Muestra todas las ventas del sistema
        - Ordenadas por fecha (más recientes primero)
        - Incluye ventas normales y a fiado
        - Información básica de cada venta
    """
    # Obtener todas las ventas ordenadas por fecha descendente
    ventas = Venta.objects.all().order_by('-fecha')
    return render(request, 'ventas/historial_ventas.html', {'ventas': ventas})
