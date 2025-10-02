import socket
import time
import os

# Lee la configuración de la base de datos desde las variables de entorno
db_host = os.environ.get('DB_HOST', 'db')
db_port = int(os.environ.get('DB_PORT', 5432))
print(f"Waiting for database at {db_host}:{db_port}...")

# Bucle infinito que intenta conectarse a la base de datos
while True:
    try:
        # Crea un socket para intentar la conexión
        with socket.create_connection((db_host, db_port), timeout=1):
            print("Database is ready!")
            break  # Si la conexión tiene éxito, rompe el bucle
    except (socket.timeout, ConnectionRefusedError):
        # Si la conexión falla, espera un segundo y vuelve a intentarlo
        print("Database isn't ready yet. Waiting...")
        time.sleep(1)