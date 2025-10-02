# Usa una imagen oficial de Python como base
FROM python:3.11-slim

# Variables de entorno para que Python funcione mejor en Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos y lo instala primero
# Esto aprovecha el caché de Docker para acelerar futuras construcciones
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copia todo el código del proyecto al directorio de trabajo
COPY . /app/