"""
Modelo de Producto para TradeInventory
Define la estructura de datos para los productos del sistema de inventario.

Este modelo representa un producto en el inventario con todas sus características:
- Información básica (nombre, descripción, precio)
- Control de stock (inicial, actual, mínimo)
- Relaciones con categorías y proveedores
- Imagen del producto
- Estado activo/inactivo
- Fechas de creación y actualización
"""

from django.db import models
from django.core.validators import MinValueValidator
from categorias.models import Categoria
from proveedores.models import Proveedor

class Producto(models.Model):
    """
    Modelo que representa un producto en el sistema de inventario
    
    Campos principales:
        - nombre: Nombre del producto
        - descripcion: Descripción detallada (opcional)
        - precio: Precio de venta del producto
        - stock_inicial: Cantidad inicial en inventario
        - stock_actual: Cantidad actual disponible
        - stock_minimo: Nivel mínimo de stock para alertas
        - categoria: Categoría a la que pertenece
        - proveedor: Proveedor del producto (opcional)
        - imagen: Imagen del producto (opcional)
        - activo: Estado activo/inactivo del producto
        - fecha_creacion: Fecha de creación del registro
        - fecha_actualizacion: Fecha de última actualización
    """
    
    # Información básica del producto
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre del producto (máximo 200 caracteres)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del producto (opcional)"
    )
    
    # Información de precios y stock
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Precio de venta del producto (mínimo 0)"
    )
    stock_inicial = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Cantidad inicial en inventario (mínimo 0)"
    )
    stock_actual = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Cantidad actual disponible en inventario (mínimo 0)"
    )
    stock_minimo = models.IntegerField(
        validators=[MinValueValidator(0)], 
        default=5,
        help_text="Nivel mínimo de stock para generar alertas (por defecto 5)"
    )
    
    # Relaciones con otros modelos
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE, 
        related_name='productos',
        help_text="Categoría a la que pertenece el producto"
    )
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='productos',
        help_text="Proveedor del producto (opcional)"
    )
    
    # Archivos y estado
    imagen = models.ImageField(
        upload_to='productos/', 
        null=True, 
        blank=True,
        help_text="Imagen del producto (opcional)"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el producto está activo en el sistema"
    )
    
    # Fechas de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del producto"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de última actualización"
    )

    def __str__(self):
        """
        Representación en string del producto
        Usado en el admin de Django y en plantillas
        """
        return self.nombre

    @property
    def stock_bajo(self):
        """
        Propiedad que indica si el stock está bajo
        Retorna True si el stock actual es menor o igual al mínimo
        
        Returns:
            bool: True si el stock está bajo, False en caso contrario
        """
        return self.stock_actual <= self.stock_minimo

    class Meta:
        """
        Configuración de metadatos del modelo
        Define cómo se comporta el modelo en el admin y en consultas
        """
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']  # Ordenar por nombre por defecto
