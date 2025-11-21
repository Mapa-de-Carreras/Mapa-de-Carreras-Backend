import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Crea (o actualiza) un usuario administrador usando variables de entorno"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")
        first_name = os.getenv("ADMIN_FIRST_NAME", "Admin")
        last_name = os.getenv("ADMIN_LAST_NAME", "User")
        legajo = os.getenv("ADMIN_LEGAJO", "ADM-001")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "legajo": legajo,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Administrador creado: {username}"))
            return

        changed = False

        if not user.is_superuser or not user.is_staff:
            user.is_superuser = True
            user.is_staff = True
            changed = True

        if user.legajo != legajo:
            user.legajo = legajo
            changed = True

        if user.email != email:
            user.email = email
            changed = True

        if changed:
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Administrador actualizado: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"El usuario {username} ya existe y ya es admin"))
