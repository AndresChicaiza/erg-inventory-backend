from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display  = ('nombre', 'email', 'rol', 'estado', 'creado_en')
    list_filter   = ('rol', 'estado')
    search_fields = ('nombre', 'email')
    ordering      = ('nombre',)
    fieldsets = (
        (None,          {'fields': ('email', 'password')}),
        ('Información', {'fields': ('nombre', 'rol', 'estado')}),
        ('Permisos',    {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields':  ('email', 'nombre', 'password1', 'password2', 'rol')}),
    )
