from django.db import models
from django.db.models import Sum, F
from productos.models import Producto
from django.utils import timezone
from decimal import Decimal

# Create your models here.

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    documento = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    @property
    def total_fiado(self):
        """
        Calcula el total de la deuda de un cliente, sumando:
        1. Fiados directos pendientes.
        2. Saldos pendientes de ventas marcadas como fiado.
        """
        # 1. Total de fiados directos (considerando abonos)
        total_fiados_directos = self.fiados.filter(pagado=False).aggregate(
            total=Sum(F('monto') - F('monto_abonado'))
        )['total'] or Decimal(0)

        # 2. Total de saldos pendientes en ventas a crédito
        # Usar importación diferida para evitar importación circular
        from ventas.models import Venta
        total_ventas_fiadas = self.venta_set.filter(es_fiado=True).aggregate(
            total=Sum(F('total') - F('monto_abonado'))
        )['total'] or Decimal(0)
        
        return total_fiados_directos + total_ventas_fiadas

    @property
    def ultimo_pago(self):
        """Obtiene la fecha del último pago realizado con información del tipo de pago"""
        # Buscar el último fiado pagado completamente
        ultimo_fiado_pagado = self.fiados.filter(pagado=True).order_by('-fecha_pago').first()
        
        # Buscar el último detalle de fiado con fecha de pago (abonos, pagos, cancelaciones)
        ultimo_detalle_pagado = self.fiados.filter(
            detalles__fecha_pago__isnull=False
        ).order_by('-detalles__fecha_pago').first()
        
        # Buscar la última venta con abono, cancelación o que ya no es fiado
        from ventas.models import Venta
        ultima_venta_con_abono = self.venta_set.filter(
            fecha_ultimo_abono__isnull=False
        ).order_by('-fecha_ultimo_abono').first()
        
        ultima_venta_cancelada = self.venta_set.filter(
            fecha_cancelacion__isnull=False
        ).order_by('-fecha_cancelacion').first()
        
        ultima_venta_pagada = self.venta_set.filter(
            es_fiado=False,
            fecha_cancelacion__isnull=True
        ).order_by('-fecha').first()
        
        # Determinar cuál es el más reciente
        fechas_pagos = []
        
        if ultimo_fiado_pagado and ultimo_fiado_pagado.fecha_pago:
            fechas_pagos.append({
                'fecha': ultimo_fiado_pagado.fecha_pago,
                'tipo': 'Fiado pagado'
            })
        
        if ultimo_detalle_pagado:
            ultimo_detalle = ultimo_detalle_pagado.detalles.filter(
                fecha_pago__isnull=False
            ).order_by('-fecha_pago').first()
            if ultimo_detalle:
                if ultimo_detalle.estado == 'cancelado':
                    fechas_pagos.append({
                        'fecha': ultimo_detalle.fecha_pago,
                        'tipo': 'Producto cancelado'
                    })
                elif ultimo_detalle.estado == 'pagado':
                    fechas_pagos.append({
                        'fecha': ultimo_detalle.fecha_pago,
                        'tipo': 'Producto pagado'
                    })
                elif ultimo_detalle.estado == 'abonado':
                    fechas_pagos.append({
                        'fecha': ultimo_detalle.fecha_pago,
                        'tipo': 'Abono'
                    })
        
        if ultima_venta_con_abono and ultima_venta_con_abono.fecha_ultimo_abono:
            fechas_pagos.append({
                'fecha': ultima_venta_con_abono.fecha_ultimo_abono,
                'tipo': 'Abono'
            })
        
        if ultima_venta_cancelada and ultima_venta_cancelada.fecha_cancelacion:
            fechas_pagos.append({
                'fecha': ultima_venta_cancelada.fecha_cancelacion,
                'tipo': 'Venta cancelada'
            })
        
        if ultima_venta_pagada and ultima_venta_pagada.fecha:
            fechas_pagos.append({
                'fecha': ultima_venta_pagada.fecha,
                'tipo': 'Venta pagada'
            })
        
        if fechas_pagos:
            # Obtener el más reciente
            ultimo_pago = max(fechas_pagos, key=lambda x: x['fecha'])
            fecha_str = ultimo_pago['fecha'].strftime("%d/%m/%Y")
            return f"{fecha_str} - {ultimo_pago['tipo']}"
        
        return "Sin pagos"

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

class Fiado(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='fiados')
    fecha = models.DateTimeField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_abonado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Fiado de {self.cliente} - {self.fecha.strftime('%Y-%m-%d')}"

    @property
    def saldo_pendiente(self):
        return self.monto - self.monto_abonado

    class Meta:
        verbose_name = 'Fiado'
        verbose_name_plural = 'Fiados'
        ordering = ['-fecha']

class DetalleFiado(models.Model):
    fiado = models.ForeignKey(Fiado, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('abonado', 'Abonado'),
            ('pagado', 'Pagado'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendiente'
    )

    def save(self, *args, **kwargs):
        # Calcular el subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    class Meta:
        verbose_name = 'Detalle de Fiado'
        verbose_name_plural = 'Detalles de Fiados'
