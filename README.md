# Mapa de Carreras - Backend

API REST para el sistema de gestión académica "Mapa de Carreras", desarrollado con Django REST Framework y PostgreSQL, y gestionado con Docker.

---

## Prerrequisitos

Asegúrate de tener instalado el siguiente software en tu máquina antes de empezar:
* [Git](https://git-scm.com/downloads)
* [Docker](https://www.docker.com/products/docker-desktop/)

---

## Puesta en Marcha

Sigue estos pasos para levantar el entorno de desarrollo completo:

1.  **Clona el repositorio y crea tu archivo `.env`**:
    ```bash
    git clone [https://github.com/yatenbueno/Mapa-de-Carreras-Backend.git](https://github.com/yatenbueno/Mapa-de-Carreras-Backend.git)
    cd Mapa-de-Carreras-Backend
    cp .env.sample .env
    ```
    *(Opcional: puedes modificar las variables en tu archivo `.env` si es necesario)*.

2.  **Levanta los servicios con Docker Compose**:
    Este comando construirá la imagen y dejará los contenedores corriendo en segundo plano.
    ```bash
    docker compose up --build -d
    ```

3.  **Ejecuta las migraciones manualmente**:
    Con los servicios corriendo, abre una terminal y ejecuta el comando `migrate` para crear las tablas en la base de datos. **Este paso es fundamental la primera vez que inicias el proyecto.**
    ```bash
    docker compose exec web python manage.py migrate
    ```

4.  **Crea un superusuario (solo la primera vez)**:
    ```bash
    docker compose exec web python manage.py createsuperuser
    ```

Una vez completados estos pasos, el servidor estará corriendo en `http://127.0.0.1:8000/` y podrás acceder al panel de administración en `http://127.0.0.1:8000/admin/`.

---

## Comandos Comunes

Para ejecutar comandos de Django, asegúrate de que los contenedores estén corriendo y usa `docker compose exec`.

* **Crear nuevas migraciones** (después de cambiar los modelos):
    ```bash
    docker compose exec web python manage.py makemigrations
    ```

* **Aplicar migraciones** (después de un `git pull` con nuevos cambios):
    ```bash
    docker compose exec web python manage.py migrate
    ```

* **Acceder al shell de Django**:
    ```bash
    docker compose exec web python manage.py shell
    ```

* **Ejecutar las pruebas automáticas**:
    ```bash
    docker compose exec web python manage.py test
    ```

---
### Nota sobre los Comandos
Este proyecto usa la sintaxis moderna de Docker Compose (V2).

**Recomendado (V2):** `docker compose`

Si ese comando no funciona, prueba a usar la versión anterior con guion:

**Legado (V1):** `docker-compose`