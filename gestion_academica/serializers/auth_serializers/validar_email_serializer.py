# En alguno de tus archivos de serializers
from rest_framework import serializers

class EmailSerializer(serializers.Serializer):
    """Un serializer simple que solo valida un email."""
    email = serializers.EmailField()