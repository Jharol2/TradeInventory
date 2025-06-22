#!/usr/bin/env python
"""
Script de gestión principal de Django para TradeInventory
Este archivo es el punto de entrada para todos los comandos de administración de Django.
Permite ejecutar comandos como runserver, migrate, createsuperuser, etc.

Uso:
    python manage.py <comando> [opciones]
    
Comandos comunes:
    - runserver: Inicia el servidor de desarrollo
    - migrate: Aplica migraciones de base de datos
    - makemigrations: Crea nuevas migraciones
    - createsuperuser: Crea un usuario administrador
    - collectstatic: Recolecta archivos estáticos
    - shell: Abre el shell interactivo de Django
"""
import os
import sys


def main():
    """
    Función principal que ejecuta comandos de Django
    Configura el entorno y ejecuta el comando especificado en la línea de comandos
    """
    # Configurar el módulo de configuración de Django
    # Esto le dice a Django dónde encontrar settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeinventory.settings')
    
    try:
        # Importar y ejecutar el comando de Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Manejar errores de importación (Django no instalado, entorno virtual no activado)
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Ejecutar el comando especificado en sys.argv
    # sys.argv contiene los argumentos de la línea de comandos
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Solo ejecutar si el script se ejecuta directamente (no importado)
    main()
