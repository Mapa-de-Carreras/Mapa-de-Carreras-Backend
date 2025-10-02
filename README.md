# Mapa de Carreras - Backend

API REST para el sistema de gestión académica "Mapa de Carreras", desarrollado con Django Rest Framework, postgreSQL

## Prerrequisitos

Asegurate de tener instalado el siguiente software localmente antes de empezar:
* [Git](https://git-scm.com/downloads)
* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/) (generalmente viene incluido con Docker Desktop)

---

## Puesta en marcha

Pasos para levantar el entorno de desarrollo:

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/yatenbueno/Mapa-de-Carreras-Backend.git](https://github.com/yatenbueno/Mapa-de-Carreras-Backend.git)
    ```

2.  **Navega a la carpeta del proyecto:**
    ```bash
    cd Mapa-de-Carreras-Backend
    ```

3.  **Levanta los servicios con Docker Compose:**
    ```bash
    docker compose up --build
    ```
    o (si usamos el modo --detach)
    ```
    docker compose up --build -d
    ```
    La primera vez, este comando descargará las imágenes necesarias, construirá el contenedor de la aplicación y ejecutará las migraciones iniciales. Después de eso, el servidor estará corriendo en `http://127.0.0.1:8000/`.

## Comandos Comunes

Para ejecutar comandos de Django (como `createsuperuser` o `makemigrations`), abre una **segunda terminal** y usa `docker compose exec`.

* **Crear un superusuario:**
    ```bash
    docker compose exec web python manage.py createsuperuser
    ```

* **Crear nuevas migraciones** (por si se modifican los modelos `models.py`):
    ```bash
    docker compose exec web python manage.py makemigrations
    ```

* **Acceder al shell de Django:**
    ```bash
    docker compose exec web python manage.py shell
    ```
---

---
### Nota 

El proyecto usa la sintaxis moderna de Docker Compose (V2)

**Recomendado (V2):** `docker compose`

Si no funciona el comando anterior, usar:

**Legado (V1):** `docker-compose`