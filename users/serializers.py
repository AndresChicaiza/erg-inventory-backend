# ── users/serializers.py ─────────────────────────────────────────────────────
from rest_framework import serializers
from .models import Usuario, Sede


class SedeSerializer(serializers.ModelSerializer):
    total_usuarios = serializers.SerializerMethodField()

    class Meta:
        model  = Sede
        fields = '__all__'

    def get_total_usuarios(self, obj):
        return obj.usuarios.filter(estado='Activo').count()


class UsuarioSerializer(serializers.ModelSerializer):
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True)
    sede_tipo   = serializers.CharField(source='sede.tipo',   read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'nombre', 'email', 'rol', 'rol_display',
            'sede', 'sede_nombre', 'sede_tipo',
            'telefono', 'estado',
            'is_staff', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UsuarioCreateSerializer(UsuarioSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ['password']


class UsuarioMeSerializer(serializers.ModelSerializer):
    """Serializer para el endpoint /auth/me/ — incluye permisos."""
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True)
    sede_tipo   = serializers.CharField(source='sede.tipo',   read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    permisos    = serializers.SerializerMethodField()

    class Meta:
        model  = Usuario
        fields = [
            'id', 'nombre', 'email', 'rol', 'rol_display',
            'sede', 'sede_nombre', 'sede_tipo',
            'telefono', 'estado', 'permisos',
        ]

    def get_permisos(self, obj):
        return {
            'ver_costos':       obj.puede_ver_costos,
            'crear_productos':  obj.puede_crear_productos,
            'aprobar_oc':       obj.puede_aprobar_oc,
            'facturar':         obj.puede_facturar,
            'es_admin':         obj.es_admin,
            'es_contador':      obj.es_contador,
            'es_vendedor':      obj.es_vendedor,
            'es_logistica':     obj.es_logistica,
            'es_jefe_fabrica':  obj.es_jefe_fabrica,
            'es_bodeguero':     obj.es_bodeguero,
            'es_rrhh':          obj.es_rrhh,
        }