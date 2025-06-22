"""
Sistema de Gestión de Clientes y Fiados para TradeInventory
Este módulo maneja todas las operaciones relacionadas con clientes y fiados:

Funcionalidades principales:
- Gestión completa de clientes (CRUD)
- Sistema de fiados directos
- Gestión de ventas a fiado
- Historial de deudas por cliente
- Abonos y pagos de fiados
- Control de estado de clientes y fiados

Características:
- Búsqueda y filtrado de clientes
- Cálculo automático de deudas pendientes
- Gestión de productos en fiados
- Historial completo de transacciones
- Interfaz para abonos parciales
- Validaciones de datos
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import Cliente, Fiado, DetalleFiado, Producto
from ventas.models import Venta, DetalleVenta
from .forms import ClienteForm, FiadoForm, DetalleFiadoFormSet
from django.utils import timezone
from decimal import Decimal

@login_required
def lista_clientes(request):
    """
    Vista principal para listar y gestionar clientes
    Muestra todos los clientes con filtros y estadísticas de fiados
    
    Args:
        request: Objeto HttpRequest con parámetros GET opcionales:
            - estado: Filtro por estado ('activo', 'inactivo', 'todos')
            - q: Término de búsqueda (nombre, teléfono, email, documento)
            
    Returns:
        HttpResponse: Renderiza la lista de clientes con estadísticas
        
    Funcionalidades:
        - Filtrado por estado activo/inactivo
        - Búsqueda por múltiples campos
        - Cálculo de estadísticas de fiados
        - Conteo de clientes activos/inactivos
        - Total de deudas pendientes
    """
    # Obtener parámetros de filtrado del request
    estado = request.GET.get('estado', 'activo')
    busqueda = request.GET.get('q', '')
    
    # Debug: imprimir parámetros para desarrollo
    print(f"DEBUG - Estado: {estado}, Búsqueda: {busqueda}")
    
    # Obtener todos los clientes y aplicar filtros
    clientes = Cliente.objects.all()
    print(f"DEBUG - Total clientes antes de filtros: {clientes.count()}")
    
    # Filtro 1: Por estado del cliente
    if estado == 'activo':
        clientes = clientes.filter(activo=True)
        print(f"DEBUG - Clientes activos: {clientes.count()}")
    elif estado == 'inactivo':
        clientes = clientes.filter(activo=False)
        print(f"DEBUG - Clientes inactivos: {clientes.count()}")
    # Si es 'todos', no se aplica filtro de estado
    
    # Filtro 2: Búsqueda por texto en múltiples campos
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) |      # Buscar en nombre
            Q(telefono__icontains=busqueda) |    # Buscar en teléfono
            Q(email__icontains=busqueda) |       # Buscar en email
            Q(documento__icontains=busqueda)     # Buscar en documento
        )
        print(f"DEBUG - Clientes después de búsqueda: {clientes.count()}")
    
    # Calcular estadísticas generales (sin filtros aplicados)
    total_clientes = Cliente.objects.count()
    clientes_activos = Cliente.objects.filter(activo=True).count()
    
    # Cálculo del total de fiados pendientes
    # Incluye tanto fiados directos como ventas a fiado
    
    # Total de fiados directos no pagados
    total_fiados_directos = Fiado.objects.filter(pagado=False).aggregate(total=Sum('monto'))['total'] or 0
    
    # Total de ventas fiadas (todas las ventas fiadas están pendientes)
    total_ventas_fiadas = Venta.objects.filter(es_fiado=True).aggregate(total=Sum('total'))['total'] or 0
    
    # Total general de fiado (suma de ambos tipos)
    total_fiado = total_fiados_directos + total_ventas_fiadas
    
    # Contar cantidad de fiados pendientes
    fiados_directos_pendientes = Fiado.objects.filter(pagado=False).count()
    ventas_fiadas_pendientes = Venta.objects.filter(es_fiado=True).count()
    fiados_pendientes = fiados_directos_pendientes + ventas_fiadas_pendientes
    
    # Preparar contexto para la plantilla
    context = {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'total_fiado': total_fiado,
        'fiados_pendientes': fiados_pendientes,
        'estado_actual': estado,
        'busqueda': busqueda,
    }
    return render(request, 'clientes/lista_clientes.html', context)

@login_required
def crear_cliente(request):
    """
    Vista para crear un nuevo cliente
    Maneja el formulario de creación de clientes
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
        
    Funcionalidades:
        - Muestra formulario vacío en GET
        - Valida y guarda datos en POST
        - Muestra mensajes de éxito/error
        - Redirige a la lista de clientes
    """
    if request.method == 'POST':
        # Procesar formulario enviado
        form = ClienteForm(request.POST)
        if form.is_valid():
            # Guardar el cliente en la base de datos
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes:lista_clientes')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario vacío para crear nuevo cliente
        form = ClienteForm()
    
    return render(request, 'clientes/crear_cliente.html', {'form': form})

@login_required
def editar_cliente(request, pk):
    """
    Vista para editar un cliente existente
    Permite modificar los datos de un cliente específico
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        pk: ID del cliente a editar
        
    Returns:
        HttpResponse: Renderiza el formulario con datos actuales o redirige después de editar
        
    Funcionalidades:
        - Carga datos existentes del cliente
        - Permite modificar todos los campos
        - Valida datos antes de guardar
        - Muestra mensajes de éxito/error
    """
    # Obtener el cliente específico o mostrar error 404 si no existe
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Procesar formulario con datos actualizados
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            # Guardar cambios en la base de datos
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes:lista_clientes')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario con datos actuales del cliente
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/crear_cliente.html', {'form': form})

@login_required
def cambiar_estado_cliente(request, pk):
    """
    Vista para activar/desactivar un cliente
    Cambia el estado activo/inactivo de un cliente específico
    
    Args:
        request: Objeto HttpRequest
        pk: ID del cliente cuyo estado se va a cambiar
        
    Returns:
        HttpResponseRedirect: Redirige a la lista de clientes
        
    Funcionalidades:
        - Invierte el estado actual del cliente
        - Guarda el cambio en la base de datos
        - Muestra mensaje de confirmación
        - Redirige a la lista de clientes
    """
    # Obtener el cliente específico o mostrar error 404 si no existe
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Invertir el estado actual (activo → inactivo, inactivo → activo)
    cliente.activo = not cliente.activo
    cliente.save()
    
    # Preparar mensaje de confirmación
    estado = "activado" if cliente.activo else "desactivado"
    messages.success(request, f'Cliente {estado} exitosamente.')
    
    # Redirigir a la lista de clientes
    return redirect('clientes:lista_clientes')

@login_required
def crear_fiado(request):
    """
    Vista para crear un nuevo fiado directo
    Permite registrar un fiado sin estar asociado a una venta
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
        
    Funcionalidades:
        - Muestra formulario para crear fiado directo
        - Valida y guarda el fiado
        - Muestra mensajes de éxito/error
        - Redirige a la lista de clientes
    """
    if request.method == 'POST':
        # Procesar formulario de fiado
        form = FiadoForm(request.POST)
        if form.is_valid():
            # Guardar el fiado en la base de datos
            form.save()
            messages.success(request, 'Fiado registrado exitosamente.')
            return redirect('clientes:lista_clientes')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario vacío para crear nuevo fiado
        form = FiadoForm()
    
    return render(request, 'clientes/crear_fiado.html', {'form': form})

@login_required
def historial_deudas(request, cliente_id):
    """
    Vista para mostrar el historial completo de deudas de un cliente
    Incluye tanto fiados directos como ventas a fiado
    
    Args:
        request: Objeto HttpRequest
        cliente_id: ID del cliente cuyo historial se va a mostrar
        
    Returns:
        HttpResponse: Renderiza el historial de deudas del cliente
        
    Funcionalidades:
        - Muestra fiados directos del cliente
        - Muestra ventas a fiado del cliente
        - Calcula totales de deudas pendientes
        - Ordena todas las deudas por fecha
        - Proporciona estadísticas del cliente
    """
    # Obtener el cliente específico o mostrar error 404 si no existe
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener fiados directos del cliente (ordenados por fecha descendente)
    fiados = Fiado.objects.filter(cliente=cliente).order_by('-fecha')
    
    # Obtener ventas fiadas del cliente (ordenadas por fecha descendente)
    ventas_fiadas = Venta.objects.filter(
        cliente=cliente, 
        es_fiado=True
    ).order_by('-fecha')
    
    # Unificar y ordenar todas las deudas por fecha para la tabla
    # Combina fiados directos y ventas fiadas en una sola lista
    deudas = sorted(
        list(fiados) + list(ventas_fiadas),
        key=lambda x: x.fecha,
        reverse=True  # Más recientes primero
    )
    
    # Calcular estadísticas combinadas del cliente
    # Total de fiados directos pendientes
    total_fiado_pendiente = fiados.filter(pagado=False).aggregate(total=Sum('monto'))['total'] or 0
    
    # Total de ventas fiadas pendientes
    total_ventas_fiadas_pendientes = ventas_fiadas.aggregate(total=Sum('total'))['total'] or 0
    
    # Total general de deuda (suma de ambos tipos)
    total_deuda = total_fiado_pendiente + total_ventas_fiadas_pendientes
    
    # Contar cantidad de fiados pendientes y pagados
    fiados_pendientes = fiados.filter(pagado=False).count() + ventas_fiadas.count()
    fiados_pagados = fiados.filter(pagado=True).count()
    
    # Preparar contexto para la plantilla
    context = {
        'cliente': cliente,
        'deudas': deudas,  # Lista unificada de todas las deudas
        'total_deuda': total_deuda,
        'fiados_pendientes': fiados_pendientes,
        'fiados_pagados': fiados_pagados,
    }
    return render(request, 'clientes/historial_deudas.html', context)

@login_required
def cambiar_estado_fiado_cliente(request, fiado_id):
    """
    Cambiar el estado de un fiado desde la sección de clientes
    Permite marcar fiados como pagados o cancelados
    
    Args:
        request: Objeto HttpRequest con parámetro POST 'accion'
        fiado_id: ID del fiado cuyo estado se va a cambiar
        
    Returns:
        HttpResponseRedirect: Redirige al historial del cliente
        
    Funcionalidades:
        - Marca fiados como pagados
        - Marca fiados como cancelados
        - Actualiza fecha de pago
        - Muestra mensajes de confirmación
    """
    
    try:
        # Obtener el fiado específico
        fiado = Fiado.objects.get(id=fiado_id)
        accion = request.POST.get('accion')
        
        if accion == 'pagar':
            # Marcar como pagado
            fiado.pagado = True
            fiado.fecha_pago = timezone.now()
            fiado.save()
            messages.success(request, f'Fiado de {fiado.cliente.nombre} marcado como PAGADO')
        elif accion == 'cancelar':
            # Marcar como cancelado (también se marca como pagado)
            fiado.pagado = True
            fiado.fecha_pago = timezone.now()
            fiado.save()
            messages.success(request, f'Fiado de {fiado.cliente.nombre} marcado como CANCELADO')
        else:
            messages.error(request, 'Acción no válida')
            
    except Fiado.DoesNotExist:
        messages.error(request, 'Fiado no encontrado')
    
    # Redirigir de vuelta al historial del cliente
    return redirect('clientes:historial_deudas', cliente_id=fiado.cliente.id)

@login_required
def obtener_precio_producto(request):
    """
    Vista AJAX para obtener el precio de un producto
    Usada en formularios dinámicos para mostrar precios automáticamente
    
    Args:
        request: Objeto HttpRequest con parámetro GET 'producto_id'
        
    Returns:
        JsonResponse: Precio del producto o error si no se encuentra
        
    Funcionalidades:
        - Busca producto por ID
        - Retorna precio en formato JSON
        - Maneja errores si el producto no existe
    """
    producto_id = request.GET.get('producto_id')
    try:
        # Obtener el producto y retornar su precio
        producto = Producto.objects.get(pk=producto_id)
        return JsonResponse({'precio': float(producto.precio)})
    except Producto.DoesNotExist:
        # Retornar error si el producto no existe
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@login_required
def detalle_fiado_cliente(request, fiado_id):
    """
    Mostrar detalles de productos de un fiado específico
    Permite ver y gestionar los productos incluidos en un fiado
    
    Args:
        request: Objeto HttpRequest
        fiado_id: ID del fiado cuyos detalles se van a mostrar
        
    Returns:
        HttpResponse: Renderiza la plantilla con detalles del fiado
        
    Funcionalidades:
        - Busca fiado por ID
        - Busca detalles del fiado
        - Calcula totales de productos y monto
        - Muestra detalles del fiado
    """
    try:
        fiado = Fiado.objects.select_related('cliente').get(id=fiado_id)
        detalles = DetalleFiado.objects.filter(fiado=fiado).select_related('producto')
        
        # Calcular totales
        total_productos = detalles.count()
        total_monto = sum(detalle.subtotal for detalle in detalles)
        
        context = {
            'fiado': fiado,
            'detalles': detalles,
            'total_productos': total_productos,
            'total_monto': total_monto,
        }
        
        return render(request, 'clientes/detalle_fiado_cliente.html', context)
        
    except Fiado.DoesNotExist:
        messages.error(request, 'Fiado no encontrado')
        return redirect('clientes:lista_clientes')

@login_required
def cambiar_estado_detalle_fiado(request, detalle_id):
    """Cambiar el estado de un detalle específico de fiado"""
    from django.utils import timezone
    
    try:
        detalle = DetalleFiado.objects.select_related('fiado', 'fiado__cliente', 'producto').get(id=detalle_id)
        accion = request.POST.get('accion')
        
        if accion == 'pagar':
            detalle.pagado = True
            detalle.estado = 'pagado'
            detalle.fecha_pago = timezone.now()
            detalle.save()
            messages.success(request, f'Producto "{detalle.producto.nombre}" marcado como PAGADO')
        elif accion == 'abonar':
            monto_abonado = request.POST.get('monto_abonado')
            if monto_abonado:
                try:
                    monto_abonado = float(monto_abonado)
                    # Siempre marcar como abonado, sin importar si llega a cero
                    detalle.pagado = False
                    detalle.estado = 'abonado'
                    detalle.fecha_pago = timezone.now()
                    detalle.save()
                    messages.success(request, f'Producto "{detalle.producto.nombre}" abonado con ${monto_abonado:.2f}')
                except ValueError:
                    messages.error(request, 'Monto de abono inválido')
            else:
                messages.error(request, 'Debe especificar un monto para el abono')
        elif accion == 'cancelar':
            detalle.pagado = True
            detalle.estado = 'cancelado'
            detalle.fecha_pago = timezone.now()
            detalle.save()
            messages.success(request, f'Producto "{detalle.producto.nombre}" marcado como CANCELADO')
        else:
            messages.error(request, 'Acción no válida')
            
    except DetalleFiado.DoesNotExist:
        messages.error(request, 'Detalle de fiado no encontrado')
    
    # Redirigir de vuelta al detalle del fiado
    return redirect('clientes:detalle_fiado_cliente', fiado_id=detalle.fiado.id)

@login_required
def abonar_fiado(request, detalle_id):
    """Vista para mostrar formulario de abono"""
    try:
        detalle = DetalleFiado.objects.select_related('fiado', 'fiado__cliente', 'producto').get(id=detalle_id)
        context = {
            'detalle': detalle,
        }
        return render(request, 'clientes/abonar_fiado.html', context)
    except DetalleFiado.DoesNotExist:
        messages.error(request, 'Detalle de fiado no encontrado')
        return redirect('clientes:lista_clientes')

@login_required
def lista_productos_deudas(request, cliente_id):
    """Mostrar todos los productos de todas las deudas del cliente en una sola lista"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener todos los detalles de fiados del cliente
    detalles_fiados = DetalleFiado.objects.filter(
        fiado__cliente=cliente
    ).select_related('fiado', 'producto').order_by('-fiado__fecha')
    
    # Obtener detalles de ventas fiadas (si existen)
    detalles_ventas = DetalleVenta.objects.filter(
        venta__cliente=cliente,
        venta__es_fiado=True
    ).select_related('venta', 'producto').order_by('-venta__fecha')
    
    # Debug: Obtener información adicional
    ventas_fiadas = Venta.objects.filter(cliente=cliente, es_fiado=True)
    fiados_del_cliente = Fiado.objects.filter(cliente=cliente)
    
    # Calcular estadísticas
    total_productos_pendientes = detalles_fiados.filter(estado='pendiente').count()
    total_productos_pagados = detalles_fiados.filter(estado='pagado').count()
    total_productos_cancelados = detalles_fiados.filter(estado='cancelado').count()
    total_productos_abonados = detalles_fiados.filter(estado='abonado').count()
    
    # Calcular montos
    total_pendiente = detalles_fiados.filter(estado='pendiente').aggregate(total=Sum('subtotal'))['total'] or 0
    total_pagado = detalles_fiados.filter(estado='pagado').aggregate(total=Sum('subtotal'))['total'] or 0
    total_cancelado = detalles_fiados.filter(estado='cancelado').aggregate(total=Sum('subtotal'))['total'] or 0
    total_abonado = detalles_fiados.filter(estado='abonado').aggregate(total=Sum('subtotal'))['total'] or 0
    
    context = {
        'cliente': cliente,
        'detalles_fiados': detalles_fiados,
        'detalles_ventas': detalles_ventas,
        'total_productos_pendientes': total_productos_pendientes,
        'total_productos_pagados': total_productos_pagados,
        'total_productos_cancelados': total_productos_cancelados,
        'total_productos_abonados': total_productos_abonados,
        'total_pendiente': total_pendiente,
        'total_pagado': total_pagado,
        'total_cancelado': total_cancelado,
        'total_abonado': total_abonado,
        # Debug info
        'debug_ventas_fiadas_count': ventas_fiadas.count(),
        'debug_fiados_count': fiados_del_cliente.count(),
        'debug_detalles_fiados_count': detalles_fiados.count(),
        'debug_detalles_ventas_count': detalles_ventas.count(),
    }
    
    return render(request, 'clientes/lista_productos_deudas.html', context)

@login_required
def deudas_simples(request, cliente_id):
    """Vista simplificada de deudas."""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener todos los fiados
    todos_fiados = Fiado.objects.filter(cliente=cliente).order_by('-fecha')
    
    # Obtener todas las ventas fiadas (que siempre están pendientes)
    ventas_fiadas = Venta.objects.filter(
        cliente=cliente, 
        es_fiado=True
    ).order_by('-fecha')
    
    # Unificar y ordenar todas las deudas por fecha para la tabla
    deudas = sorted(
        list(todos_fiados) + list(ventas_fiadas),
        key=lambda x: x.fecha,
        reverse=True
    )
    
    # Calcular el total de la deuda pendiente
    total_fiados_pendientes = todos_fiados.filter(pagado=False).aggregate(total=Sum('monto'))['total'] or 0
    total_ventas_fiadas = ventas_fiadas.aggregate(total=Sum('total'))['total'] or 0
    total_deuda_pendiente = total_fiados_pendientes + total_ventas_fiadas
    
    context = {
        'cliente': cliente,
        'deudas': deudas,
        'total_deuda_pendiente': total_deuda_pendiente,
    }
    
    return render(request, 'clientes/deudas_simples.html', context)

@login_required
def abonar_deuda_simple(request, detalle_id):
    """Vista para abonar una deuda específica (toda la cuenta)"""
    detalle = get_object_or_404(DetalleFiado, id=detalle_id)
    fiado = detalle.fiado
    cliente = fiado.cliente
    
    # Obtener todos los detalles del fiado para calcular el total
    todos_detalles = DetalleFiado.objects.filter(fiado=fiado)
    total_fiado = todos_detalles.aggregate(total=Sum('subtotal'))['total'] or 0
    
    if request.method == 'POST':
        monto_abono = request.POST.get('monto_abono')
        if monto_abono:
            try:
                monto_abono = float(monto_abono)
                if monto_abono > 0 and monto_abono <= total_fiado:
                    # Aplicar el abono a toda la cuenta
                    if monto_abono >= total_fiado:
                        # Si paga el total, marcar todo como pagado
                        for det in todos_detalles:
                            det.estado = 'pagado'
                            det.pagado = True
                            det.fecha_pago = timezone.now()
                            det.save()
                        fiado.pagado = True
                        fiado.save()
                        messages.success(request, f'Fiado pagado completamente')
                    else:
                        # Si abona parcialmente, marcar como abonado
                        for det in todos_detalles:
                            det.estado = 'abonado'
                            det.pagado = False
                            det.fecha_pago = None
                            det.save()
                        messages.success(request, f'Abono de ${monto_abono:.2f} registrado para toda la cuenta')
                    
                    return redirect('clientes:deudas_simples', cliente_id=cliente.id)
                else:
                    messages.error(request, 'El monto del abono debe ser mayor a 0 y menor o igual al total del fiado')
            except ValueError:
                messages.error(request, 'Por favor ingrese un monto válido')
    
    context = {
        'detalle': detalle,
        'cliente': cliente,
        'fiado': fiado,
        'todos_detalles': todos_detalles,
        'total_fiado': total_fiado,
    }
    return render(request, 'clientes/abonar_deuda_simple.html', context)

@login_required
def abonar_venta_simple(request, detalle_id):
    """Vista para abonar una venta fiada específica (toda la cuenta)"""
    from ventas.models import DetalleVenta
    detalle = get_object_or_404(DetalleVenta, id=detalle_id)
    venta = detalle.venta
    cliente = venta.cliente
    
    # Obtener todos los detalles de la venta para calcular el total
    todos_detalles = DetalleVenta.objects.filter(venta=venta)
    total_venta = todos_detalles.aggregate(total=Sum('subtotal'))['total'] or 0
    
    if request.method == 'POST':
        monto_abono = request.POST.get('monto_abono')
        if monto_abono:
            try:
                monto_abono = float(monto_abono)
                if monto_abono > 0 and monto_abono <= total_venta:
                    # Registrar la fecha del abono
                    venta.fecha_ultimo_abono = timezone.now()
                    
                    # Aplicar el abono a toda la cuenta
                    if monto_abono >= total_venta:
                        # Si paga el total, cambiar a venta normal
                        venta.es_fiado = False
                        venta.fecha_cancelacion = timezone.now()
                        venta.save()
                        messages.success(request, f'Venta pagada completamente')
                    else:
                        # Si abona parcialmente, mantener como fiada
                        venta.save()
                        messages.success(request, f'Abono de ${monto_abono:.2f} registrado para toda la cuenta')
                    
                    return redirect('clientes:deudas_simples', cliente_id=cliente.id)
                else:
                    messages.error(request, 'El monto del abono debe ser mayor a 0 y menor o igual al total de la venta')
            except ValueError:
                messages.error(request, 'Por favor ingrese un monto válido')
    
    context = {
        'detalle': detalle,
        'cliente': cliente,
        'venta': venta,
        'todos_detalles': todos_detalles,
        'total_venta': total_venta,
    }
    return render(request, 'clientes/abonar_venta_simple.html', context)

@login_required
def productos_deuda(request, tipo, id):
    """Muestra los productos de una deuda y maneja abonos y cancelaciones."""
    
    # Determinar el modelo y obtener la deuda
    if tipo == 'fiado':
        deuda = get_object_or_404(Fiado, id=id)
        detalles = DetalleFiado.objects.filter(fiado=deuda).select_related('producto')
        es_venta = False
    elif tipo == 'venta':
        deuda = get_object_or_404(Venta, id=id)
        detalles = DetalleVenta.objects.filter(venta=deuda).select_related('producto')
        es_venta = True
    else:
        # Manejar un tipo no válido si es necesario
        return redirect('clientes:lista_clientes')
        
    cliente = deuda.cliente

    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'abonar':
            monto_str = request.POST.get('monto_abonado', '0')
            try:
                monto_abono = Decimal(monto_str)
                saldo_pendiente = deuda.saldo_pendiente
                
                if 0 < monto_abono <= saldo_pendiente:
                    deuda.monto_abonado += monto_abono
                    
                    # Si es una venta, registrar la fecha del abono
                    if tipo == 'venta':
                        deuda.fecha_ultimo_abono = timezone.now()
                    
                    deuda.save()
                    messages.success(request, f'Abono de ${monto_abono} registrado correctamente.')
                    
                    # Si el saldo queda en cero o menos, marcar como pagado
                    if deuda.saldo_pendiente <= 0:
                        if tipo == 'fiado':
                            deuda.pagado = True
                            deuda.fecha_pago = timezone.now()
                        elif tipo == 'venta':
                            deuda.es_fiado = False
                        deuda.save()
                        messages.info(request, 'La deuda ha sido saldada por completo.')
                        return redirect('clientes:deudas_simples', cliente_id=cliente.id)
                else:
                    messages.error(request, 'El monto a abonar es inválido.')
            except (ValueError, TypeError):
                messages.error(request, 'Por favor, ingrese un monto numérico válido.')
            
        elif accion == 'cancelar':
            if tipo == 'fiado':
                deuda.pagado = True
                deuda.fecha_pago = timezone.now()
            elif tipo == 'venta':
                deuda.es_fiado = False
                deuda.fecha_cancelacion = timezone.now()
            deuda.save()
            messages.success(request, 'La deuda ha sido cancelada exitosamente.')
            return redirect('clientes:deudas_simples', cliente_id=cliente.id)

        return redirect('clientes:productos_deuda', tipo=tipo, id=id)

    context = {
        'cliente': cliente,
        'deuda': deuda,
        'detalles': detalles,
        'tipo': tipo,
        'es_venta': es_venta,
    }
    
    return render(request, 'clientes/productos_deuda.html', context)

@login_required
def cambiar_estado_detalle_venta(request, detalle_id):
    """Cambiar el estado de un detalle específico de venta fiada"""
    from django.utils import timezone
    from ventas.models import DetalleVenta
    
    try:
        detalle = DetalleVenta.objects.select_related('venta', 'venta__cliente', 'producto').get(id=detalle_id)
        accion = request.POST.get('accion')
        
        if accion == 'abonar':
            monto_abonado = request.POST.get('monto_abonado')
            if monto_abonado:
                try:
                    monto_abonado = float(monto_abonado)
                    # Aplicar el abono a la venta completa
                    venta = detalle.venta
                    venta.monto_abonado += monto_abonado
                    venta.fecha_ultimo_abono = timezone.now()
                    
                    # Si el saldo queda en cero o menos, cambiar a venta normal
                    if venta.saldo_pendiente <= 0:
                        venta.es_fiado = False
                        venta.fecha_cancelacion = timezone.now()
                        venta.save()
                        messages.success(request, f'Venta pagada completamente. Producto "{detalle.producto.nombre}" incluido.')
                    else:
                        messages.success(request, f'Abono de ${monto_abonado:.2f} registrado. Producto "{detalle.producto.nombre}" incluido.')
                        
                except ValueError:
                    messages.error(request, 'Monto de abono inválido')
            else:
                messages.error(request, 'Debe especificar un monto para el abono')
        elif accion == 'cancelar':
            # Cancelar la venta completa
            venta = detalle.venta
            venta.es_fiado = False
            venta.save()
            messages.success(request, f'Venta cancelada. Producto "{detalle.producto.nombre}" incluido.')
        else:
            messages.error(request, 'Acción no válida')
            
    except DetalleVenta.DoesNotExist:
        messages.error(request, 'Detalle de venta no encontrado')
    
    # Redirigir de vuelta a la página de productos de deuda
    return redirect('clientes:productos_deuda', tipo='venta', id=detalle.venta.id)

@login_required
def historial_abonos(request, cliente_id):
    """Mostrar el historial de abonos de un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener abonos de fiados directos
    abonos_fiados = DetalleFiado.objects.filter(
        fiado__cliente=cliente,
        fecha_pago__isnull=False
    ).select_related('fiado', 'producto').order_by('-fecha_pago')
    
    # Obtener abonos de ventas fiadas
    from ventas.models import Venta
    abonos_ventas = Venta.objects.filter(
        cliente=cliente,
        fecha_ultimo_abono__isnull=False
    ).order_by('-fecha_ultimo_abono')
    
    # Obtener cancelaciones de ventas
    cancelaciones_ventas = Venta.objects.filter(
        cliente=cliente,
        fecha_cancelacion__isnull=False
    ).order_by('-fecha_cancelacion')
    
    # Obtener fiados pagados completamente
    fiados_pagados = Fiado.objects.filter(
        cliente=cliente,
        pagado=True,
        fecha_pago__isnull=False
    ).order_by('-fecha_pago')
    
    # Unificar todos los movimientos por fecha
    movimientos = []
    
    # Agregar abonos de fiados
    for abono in abonos_fiados:
        movimientos.append({
            'fecha': abono.fecha_pago,
            'tipo': 'Abono',
            'descripcion': f'Producto: {abono.producto.nombre}',
            'monto': abono.subtotal,
            'estado': abono.estado,
            'origen': 'Fiado',
            'origen_id': abono.fiado.id
        })
    
    # Agregar abonos de ventas
    for venta in abonos_ventas:
        movimientos.append({
            'fecha': venta.fecha_ultimo_abono,
            'tipo': 'Abono',
            'descripcion': f'Venta #{venta.id}',
            'monto': venta.monto_abonado,
            'estado': 'Abonado',
            'origen': 'Venta',
            'origen_id': venta.id
        })
    
    # Agregar cancelaciones de ventas
    for venta in cancelaciones_ventas:
        movimientos.append({
            'fecha': venta.fecha_cancelacion,
            'tipo': 'Cancelación',
            'descripcion': f'Venta #{venta.id}',
            'monto': venta.total,
            'estado': 'Cancelado',
            'origen': 'Venta',
            'origen_id': venta.id
        })
    
    # Agregar fiados pagados completamente
    for fiado in fiados_pagados:
        movimientos.append({
            'fecha': fiado.fecha_pago,
            'tipo': 'Pago completo',
            'descripcion': f'Fiado #{fiado.id}',
            'monto': fiado.monto,
            'estado': 'Pagado',
            'origen': 'Fiado',
            'origen_id': fiado.id
        })
    
    # Ordenar por fecha (más reciente primero)
    movimientos.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Calcular estadísticas
    total_abonos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Abono')
    total_cancelaciones = sum(m['monto'] for m in movimientos if m['tipo'] == 'Cancelación')
    total_pagos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Pago completo')
    
    context = {
        'cliente': cliente,
        'movimientos': movimientos,
        'total_abonos': total_abonos,
        'total_cancelaciones': total_cancelaciones,
        'total_pagos': total_pagos,
        'total_movimientos': len(movimientos)
    }
    
    return render(request, 'clientes/historial_abonos.html', context)
