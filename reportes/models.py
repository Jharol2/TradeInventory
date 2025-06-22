from django.db import models
from django.contrib.auth.models import User

class ConfiguracionReporte(models.Model):
    PERIODO_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
    ]
    
    TIPO_REPORTE_CHOICES = [
        ('ventas', 'Reporte de Ventas'),
        ('productos', 'Reporte de Productos'),
        ('clientes', 'Reporte de Clientes'),
        ('inventario', 'Reporte de Inventario'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES)
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    activo = models.BooleanField(default=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.get_periodo_display()}"

class HistorialReporte(models.Model):
    configuracion = models.ForeignKey(ConfiguracionReporte, on_delete=models.CASCADE)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='reportes/', null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Historial de Reporte'
        verbose_name_plural = 'Historial de Reportes'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.configuracion} - {self.fecha_generacion.strftime('%Y-%m-%d %H:%M')}"
