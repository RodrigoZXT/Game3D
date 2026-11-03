# Operación Limpieza Táctica 3D

Videojuego 3D (three.js) con servidor en Python (Flask). Proyecto de Estructura de Datos.

## Qué hace Python
- Genera el mapa (edificios con puerta, coberturas y barriles) y las oleadas de enemigos.
- Controla el cambio de arma con una **lista circular doblemente enlazada** (`ListaCircular`).
- Arma el orden de los enemigos con una **cola** (`Cola`) y guarda el top 5 en una **lista enlazada ordenada** (`Ranking`).

## Archivos
- `app.py`: servidor Flask y estructuras de datos.
- `index.html`: escena 3D y combate (three.js).
- `requirements.txt`: dependencias (flask, gunicorn).
- `Procfile` y `render.yaml`: arranque en Render / Koyeb.

## Ejecutar en local
    pip install -r requirements.txt
    python app.py
    # abrir http://127.0.0.1:5000

## Desplegar en PythonAnywhere (plan gratuito Beginner)
1. Crear una cuenta gratuita en pythonanywhere.com.
2. Subir el proyecto: en la pestaña Consoles abrir una consola Bash y clonar el repositorio con `git clone https://github.com/USUARIO/REPOSITORIO.git juego3d` (o subir los archivos desde la pestaña Files).
3. En la pestaña Web: Add a new web app > Manual configuration > versión de Python más reciente.
4. En Web, poner Source code y Working directory en `/home/USUARIO/juego3d`.
5. Abrir el archivo de configuración WSGI y dejar solo este contenido:

        import sys
        ruta = '/home/USUARIO/juego3d'
        if ruta not in sys.path:
            sys.path.insert(0, ruta)
        from app import app as application

6. Presionar el botón verde Reload y abrir `https://USUARIO.pythonanywhere.com`.
7. Los registros se ven en la pestaña Web > Log files (Error log y Server log).
8. En el plan gratuito hay que presionar "Run until..." / Extend de vez en cuando para que la aplicación no expire.

(Los archivos `Procfile` y `render.yaml` solo se usan en Render o Koyeb; en PythonAnywhere no hacen falta.)

## Controles
WASD mover · Mouse apuntar y disparar · 1-4, Tab o rueda cambiar arma · Shift dash · R recargar · P o Esc pausa
