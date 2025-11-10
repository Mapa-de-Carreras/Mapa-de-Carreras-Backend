# gestion_academica/serializers/auth_serializers/enviar_codigo_verificacion_serializer.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from random import randint

User = get_user_model()


class EnviarCodigoVerificacionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    contexto = serializers.ChoiceField(
        choices=["registro", "recuperacion", "reenviar_activacion"])

    def validate(self, data):
        """ Validación centralizada antes de enviar el código. """
        email = data.get('email')
        contexto = data.get('contexto')

        if contexto == "recuperacion":
            # Para recuperación, el email SÍ debe existir
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "Este correo no está registrado."})

        elif contexto == "reenviar_activacion":
            # Para reenviar, el email SÍ debe existir Y estar INACTIVO
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "Este correo no está registrado."})

            if user.is_active:
                raise serializers.ValidationError(
                    {"error": "Esta cuenta ya ha sido activada."})

        # Si el contexto es "registro", no se valida nada aquí (lo hace la vista de registro)
        return data

    def enviar_codigo(self):
        """
        Método único para generar, guardar en caché y enviar el email.
        Se llama después de que .is_valid() haya corrido las validaciones.
        """
        # .validated_data solo existe después de llamar a .is_valid()
        email = self.validated_data['email']
        contexto = self.validated_data['contexto']

        # --- INICIO DE LÓGICA COMPARTIDA ---

        # 1. Generamos un código de verificación (número aleatorio de 6 dígitos)
        verification_code = randint(100000, 999999)

        # 2. Guardamos el código en caché (expira en 5 minutos)
        cache.set(f"verification_code_{email}", verification_code, timeout=300)

        # 3. Elegir el cuerpo del mensaje según el contexto
        if contexto == "registro" or contexto == "reenviar_activacion":
            subject = "Confirmación de registro - Mapa de Carreras"
            message_body = (
                f"Para completar tu registro, por favor ingresá el siguiente código de verificación:\n\n"
                f"🔐 Código:\n\n"
                f"{verification_code}\n\n"
            )
        else:  # recuperación
            subject = "Recuperación de contraseña - Mapa de Carreras"
            message_body = (
                f"Recibimos una solicitud para restablecer tu contraseña en Mapa de Carreras.\n\n"
                f"🔐 Tu código de recuperación es:\n\n"
                f"{verification_code}\n\n"
            )

        # Plantilla de mensaje completa sin importar la operación
        message = (
            f"Hola,\n\n"
            f"{message_body}\n\n"
            f"Este código es válido por 5 minutos.\n\n"
            f"Si no solicitaste esta operación, podés ignorar este mensaje.\n\n"
            f"Saludos,\n"
            f"El equipo de Mapa de Carreras"
        )

        # 4. Enviar el correo
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        # --- FIN DE LÓGICA COMPARTIDA ---

        # Respuesta estándar
        response_data = {"message": "Código de verificación enviado al correo"}

        # Si estamos en DEBUG, añadimos el código a la respuesta para testear
        if settings.DEBUG:
            response_data['debug_code'] = verification_code

        return response_data
