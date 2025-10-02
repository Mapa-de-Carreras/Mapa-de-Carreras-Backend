#!/bin/sh

# Espera a que la base de datos esté lista
echo "Waiting for database..."
python wait_for_db.py

# Aplica las migraciones de la base de datos
echo "Applying database migrations..."
python manage.py migrate

# Ejecuta el comando principal
exec "$@"