from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.lista_reportes, name='lista_reportes'),
    path('productos/', views.reporte_productos, name='reporte_productos'),
    path('ventas/', views.reporte_ventas, name='reporte_ventas'),
    path('clientes/', views.reporte_clientes, name='reporte_clientes'),
    path('proveedores/', views.reporte_proveedores, name='reporte_proveedores'),
    path('fiados/', views.reporte_fiados, name='reporte_fiados'),
    path('fiados/<int:fiado_id>/cambiar-estado/', views.cambiar_estado_fiado, name='cambiar_estado_fiado'),
    path('fiados/<int:fiado_id>/detalle/', views.detalle_fiado, name='detalle_fiado'),
    path('categorias/', views.reporte_categorias, name='reporte_categorias'),
] 