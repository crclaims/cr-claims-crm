# CR Claims Resolution - Production Prepared

Este paquete deja el starter preparado para el último tramo de producción.

## Preparado
- PostgreSQL real vía DATABASE_URL
- SECRET_KEY generada
- credenciales admin temporales generadas
- placeholders para S3/cloud storage
- Google Maps real por API key
- render.yaml para Render
- Dockerfile y gunicorn

## Credenciales generadas
Admin: JD.claimsresolution@gmail.com
Temporary password: 2lau#NnQYR2qIojbKphS

## IMPORTANTE
No pude desplegarlo en internet desde este entorno porque no tengo acceso a tu cuenta de Render/Railway/VPS ni a tus claves de Google Maps/S3/PostgreSQL.
Pero el código quedó listo para cargar esas credenciales y desplegarlo.

## Inicio rápido
1. Copia .env.example a .env
2. Completa DATABASE_URL / GOOGLE_MAPS_API_KEY / AWS_*
3. pip install -r requirements.txt
4. python manage.py
5. python run.py

## URL local
http://127.0.0.1:8000/login
