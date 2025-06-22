from django.urls import path
from . import views

app_name = 'categorias'

urlpatterns = [
    path('', views.lista_categorias, name='lista_categorias'),
    path('crear/', views.crear_categoria, name='crear_categoria'),
    path('editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado, name='cambiar_estado'),
    path('detalle/<int:pk>/', views.detalle_categoria, name='detalle_categoria'),
] 