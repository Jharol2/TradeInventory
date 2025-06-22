from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),
    path('crear/', views.crear_cliente, name='crear_cliente'),
    path('editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado_cliente, name='cambiar_estado_cliente'),
    path('fiar/', views.crear_fiado, name='crear_fiado'),
    path('historial-deudas/<int:cliente_id>/', views.historial_deudas, name='historial_deudas'),
    path('historial-abonos/<int:cliente_id>/', views.historial_abonos, name='historial_abonos'),
    path('deudas/<int:cliente_id>/', views.deudas_simples, name='deudas_simples'),
    path('productos-deuda/<str:tipo>/<int:id>/', views.productos_deuda, name='productos_deuda'),
    path('abonar-deuda/<int:detalle_id>/', views.abonar_deuda_simple, name='abonar_deuda_simple'),
    path('abonar-venta/<int:detalle_id>/', views.abonar_venta_simple, name='abonar_venta_simple'),
    path('productos-deudas/<int:cliente_id>/', views.lista_productos_deudas, name='lista_productos_deudas'),
    path('fiado/<int:fiado_id>/cambiar-estado/', views.cambiar_estado_fiado_cliente, name='cambiar_estado_fiado'),
    path('fiado/<int:fiado_id>/detalle/', views.detalle_fiado_cliente, name='detalle_fiado_cliente'),
    path('detalle-fiado/<int:detalle_id>/cambiar-estado/', views.cambiar_estado_detalle_fiado, name='cambiar_estado_detalle_fiado'),
    path('detalle-fiado/<int:detalle_id>/abonar/', views.abonar_fiado, name='abonar_fiado'),
    path('detalle-venta/<int:detalle_id>/cambiar-estado/', views.cambiar_estado_detalle_venta, name='cambiar_estado_detalle_venta'),
] 