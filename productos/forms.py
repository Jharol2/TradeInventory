"""
Formulario para la gestión de productos en TradeInventory
Este módulo define el formulario utilizado para crear y editar productos.

El formulario incluye:
- Todos los campos del modelo Producto
- Widgets personalizados con clases CSS de Bootstrap
- Etiquetas en español
- Validaciones automáticas del modelo
- Manejo de archivos de imagen
"""

from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar productos
    
    Este formulario extiende ModelForm de Django para proporcionar:
    - Validación automática basada en el modelo Producto
    - Widgets personalizados con estilos Bootstrap
    - Etiquetas en español
    - Manejo de archivos de imagen
    
    Campos incluidos:
        - nombre: Campo de texto para el nombre del producto
        - descripcion: Área de texto para la descripción
        - precio: Campo numérico con validación de precio
        - stock_inicial: Cantidad inicial en inventario
        - stock_actual: Cantidad actual disponible
        - stock_minimo: Nivel mínimo de stock
        - categoria: Selector de categoría
        - proveedor: Selector de proveedor (opcional)
        - imagen: Subida de archivo de imagen
        - activo: Selector de estado activo/inactivo
    """
    
    class Meta:
        """
        Configuración del formulario basada en el modelo Producto
        Define qué campos incluir, widgets y etiquetas
        """
        model = Producto
        # Campos del modelo que se incluyen en el formulario
        fields = [
            'nombre', 
            'descripcion', 
            'precio', 
            'stock_inicial', 
            'stock_actual', 
            'stock_minimo', 
            'categoria', 
            'proveedor', 
            'imagen', 
            'activo'
        ]
        
        # Widgets personalizados con clases CSS de Bootstrap
        widgets = {
            # Campo de nombre con placeholder y clase Bootstrap
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre del producto'
            }),
            
            # Área de texto para descripción con múltiples líneas
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descripción del producto'
            }),
            
            # Campo numérico para precio con validación de decimales
            'precio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',  # Permite decimales con 2 lugares
                'min': '0'       # No permite valores negativos
            }),
            
            # Campo numérico para stock inicial
            'stock_inicial': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'       # No permite valores negativos
            }),
            
            # Campo numérico para stock actual
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'       # No permite valores negativos
            }),
            
            # Campo numérico para stock mínimo
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'       # No permite valores negativos
            }),
            
            # Selector de categoría con estilo Bootstrap
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Selector de proveedor con estilo Bootstrap
            'proveedor': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Campo de subida de archivo para imagen
            'imagen': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            
            # Selector de estado con opciones personalizadas
            'activo': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (True, 'Activo'), 
                (False, 'Inactivo')
            ]),
        }
        
        # Etiquetas personalizadas en español para cada campo
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'stock_inicial': 'Stock Inicial',
            'stock_actual': 'Stock Actual',
            'stock_minimo': 'Stock Mínimo',
            'categoria': 'Categoría',
            'proveedor': 'Proveedor',
            'imagen': 'Imagen del Producto',
            'activo': 'Estado',
        } 