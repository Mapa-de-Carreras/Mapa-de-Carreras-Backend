from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from gestion_academica.permissions import EsAdministrador
from gestion_academica.tasks import tasks # Importamos tu archivo de tareas

class DebugEjecutarNotificacionesView(APIView):
    """
    Endpoint SÓLO PARA DESARROLLO.
    Permite a un Admin ejecutar manualmente la tarea de
    notificación de vencimientos de designaciones.
    """
    permission_classes = [EsAdministrador]

    def post(self, request, *args, **kwargs):
        try:
            print("--- EJECUTANDO TAREA DE NOTIFICACIÓN (MANUAL) ---")
            
            # Aquí llamamos a la función de tu tasks.py
            tasks.notificar_vencimientos_designaciones()
            
            print("--- TAREA DE NOTIFICACIÓN (MANUAL) COMPLETADA ---")
            
            return Response(
                {"status": "Tarea ejecutada correctamente."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"La tarea falló: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )