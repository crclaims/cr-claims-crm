# Despliegue rápido en Render

1. Subir este proyecto a GitHub.
2. En Render crear:
   - Web Service
   - PostgreSQL database
3. Conectar el repositorio.
4. Agregar variables:
   - SECRET_KEY
   - DATABASE_URL
   - UPLOAD_FOLDER=instance/uploads
5. Build command:
   pip install -r requirements.txt
6. Start command:
   gunicorn wsgi:app
7. Ejecutar una vez:
   python manage.py

Luego entrar con los usuarios demo o crear nuevos usuarios en base de datos.
