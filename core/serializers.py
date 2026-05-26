from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source='usuario.nombre')
    usuario_rol    = serializers.ReadOnlyField(source='usuario.rol')
    usuario_email  = serializers.ReadOnlyField(source='usuario.email')
    
    class Meta:
        model  = AuditLog
        fields = '__all__'
