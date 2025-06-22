@echo off
REM ===================================================================
REM Script de inicio automático para TradeInventory
REM Este archivo batch automatiza el proceso de inicio del servidor Django
REM 
REM Funcionalidad:
REM 1. Cambia al directorio del proyecto
REM 2. Activa el entorno virtual de Python
REM 3. Inicia el servidor de desarrollo Django
REM 4. Muestra información útil al usuario
REM
REM Uso: Doble clic en este archivo para iniciar el servidor
REM ===================================================================

echo Iniciando TradeInventory...
echo.

REM Cambiar al directorio del proyecto TradeInventory
REM /d permite cambiar de unidad si es necesario
cd /d C:\TradeInventory

REM Activar el entorno virtual de Python
REM Esto asegura que se usen las dependencias correctas del proyecto
call venv\Scripts\activate

echo Servidor iniciado en http://127.0.0.1:8000/
echo Presiona Ctrl+C para detener el servidor
echo.

REM Iniciar el servidor de desarrollo Django
REM runserver inicia el servidor en modo desarrollo
python manage.py runserver

REM Pausar al final para que el usuario pueda ver cualquier mensaje de error
pause 