"""
Script de configuración inicial de ERG Inventory para Suministros Dacar S.A.S.

Ejecutar UNA SOLA VEZ después de las migraciones:
    python manage.py shell < setup_inicial.py

O como comando de management:
    python manage.py setup_inicial
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Usuario, Sede
from configuracion.models import ConfiguracionEmpresa, TarifaReteICA, TarifaRetefuente


def crear_sedes():
    sedes = [
        {'nombre': 'Oficina Principal',   'tipo': 'OFICINA',   'ciudad': 'Cali', 'direccion': 'CR 17 G # 25 – 78'},
        {'nombre': 'Fábrica',             'tipo': 'FABRICA',   'ciudad': 'Cali', 'direccion': ''},
        {'nombre': 'Club del Asado Sur',  'tipo': 'TIENDA',    'ciudad': 'Cali', 'direccion': ''},
        {'nombre': 'Club del Asado Norte','tipo': 'TIENDA',    'ciudad': 'Cali', 'direccion': ''},
        {'nombre': 'Mercadeo',            'tipo': 'MERCADEO',  'ciudad': 'Cali', 'direccion': ''},
        {'nombre': 'Logística',           'tipo': 'LOGISTICA', 'ciudad': 'Cali', 'direccion': ''},
    ]
    created = []
    for s in sedes:
        sede, c = Sede.objects.get_or_create(nombre=s['nombre'], defaults=s)
        created.append(f"  {'✅ Creada' if c else '⚠️  Ya existe'}: {sede.nombre} ({sede.tipo})")
    return created


def crear_admin():
    email    = 'admin@erg.com'
    password = 'solocali'
    nombre   = 'Administrador ERG'

    sede_oficina = Sede.objects.filter(tipo='OFICINA').first()

    if Usuario.objects.filter(email=email).exists():
        return [f'  ⚠️  Admin ya existe: {email}']

    admin = Usuario.objects.create_superuser(
        email=email,
        nombre=nombre,
        password=password,
        rol='Administrador',
        sede=sede_oficina,
    )
    return [f'  ✅ Admin creado: {admin.email} / {password}']


def crear_configuracion():
    config, created = ConfiguracionEmpresa.objects.get_or_create(
        pk=1,
        defaults={
            'nit':                  '901334172',
            'digito_verificacion':  '0',
            'razon_social':         'SUMINISTROS DACAR S.A.S.',
            'nombre_comercial':     'VOLCANO ASADORES',
            'direccion':            'CR 17 G # 25 – 78',
            'ciudad':               'Cali',
            'departamento':         'Valle del Cauca',
            'telefono':             '316 691 4910',
            'telefono2':            '312 780 1986',
            'email':                'suministrosdacar@gmail.com',
            'email_notificaciones': 'chicaizapipe@gmail.com',
            'ciiu':                 '4659',
            'regimen':              'Responsable de IVA',
            'agente_retenedor':     True,
            'gran_contribuyente':   False,
            'prefijo_factura':      'FACT',
            'consecutivo_actual':   1,
            'iva_default':          19.00,
        }
    )
    return [f"  {'✅ Creada' if created else '⚠️  Ya existe'}: Configuración de {config.razon_social}"]


def crear_tarifas_retefuente():
    tarifas = [
        {'concepto': 'COMPRAS',       'descripcion': 'Compras generales de bienes',          'tarifa_porcentaje': 2.50,  'cuantia_minima': 1_248_000},
        {'concepto': 'SERVICIOS',     'descripcion': 'Servicios generales',                   'tarifa_porcentaje': 4.00,  'cuantia_minima': 160_000},
        {'concepto': 'HONORARIOS',    'descripcion': 'Honorarios y comisiones',               'tarifa_porcentaje': 11.00, 'cuantia_minima': 0},
        {'concepto': 'ARRENDAMIENTO', 'descripcion': 'Arrendamiento de bienes inmuebles',     'tarifa_porcentaje': 3.50,  'cuantia_minima': 0},
        {'concepto': 'TRANSPORTE',    'descripcion': 'Transporte de carga',                   'tarifa_porcentaje': 1.00,  'cuantia_minima': 160_000},
        {'concepto': 'OTROS',         'descripcion': 'Otros conceptos',                       'tarifa_porcentaje': 2.50,  'cuantia_minima': 160_000},
    ]
    created_list = []
    for t in tarifas:
        obj, c = TarifaRetefuente.objects.get_or_create(concepto=t['concepto'], defaults={**t, 'uvt_referencia': 2025})
        created_list.append(f"  {'✅' if c else '⚠️ '} Retefuente {obj.get_concepto_display()}: {obj.tarifa_porcentaje}%")
    return created_list


def crear_tarifas_reteica():
    """
    Tarifas ReteICA para las principales ciudades de Colombia.
    Actividad 4659 (Comercio maquinaria).
    """
    tarifas = [
        # Cali
        {'ciudad': 'Cali',     'departamento': 'Valle del Cauca', 'ciiu_desde': '4659', 'ciiu_hasta': '4659', 'descripcion': 'Comercio maquinaria - Cali',    'tarifa_por_mil': 9.660},
        {'ciudad': 'Cali',     'departamento': 'Valle del Cauca', 'ciiu_desde': '5611', 'ciiu_hasta': '5619', 'descripcion': 'Restaurantes y similares - Cali','tarifa_por_mil': 9.660},
        {'ciudad': 'Cali',     'departamento': 'Valle del Cauca', 'ciiu_desde': '0000', 'ciiu_hasta': '9999', 'descripcion': 'General - Cali',                 'tarifa_por_mil': 9.660},
        # Bogotá
        {'ciudad': 'Bogotá',   'departamento': 'Cundinamarca',    'ciiu_desde': '0000', 'ciiu_hasta': '9999', 'descripcion': 'General - Bogotá',               'tarifa_por_mil': 11.040},
        # Medellín
        {'ciudad': 'Medellín', 'departamento': 'Antioquia',       'ciiu_desde': '0000', 'ciiu_hasta': '9999', 'descripcion': 'General - Medellín',             'tarifa_por_mil': 10.000},
        # Barranquilla
        {'ciudad': 'Barranquilla','departamento':'Atlántico',      'ciiu_desde': '0000', 'ciiu_hasta': '9999', 'descripcion': 'General - Barranquilla',         'tarifa_por_mil': 8.000},
        # Bucaramanga
        {'ciudad': 'Bucaramanga','departamento': 'Santander',     'ciiu_desde': '0000', 'ciiu_hasta': '9999', 'descripcion': 'General - Bucaramanga',          'tarifa_por_mil': 7.000},
    ]
    created_list = []
    for t in tarifas:
        obj, c = TarifaReteICA.objects.get_or_create(
            ciudad=t['ciudad'], ciiu_desde=t['ciiu_desde'],
            defaults=t
        )
        created_list.append(f"  {'✅' if c else '⚠️ '} ReteICA {obj.ciudad}: {obj.tarifa_por_mil}‰")
    return created_list


def main():
    print('\n' + '='*55)
    print('  ERG INVENTORY — Setup inicial Suministros Dacar SAS')
    print('='*55)

    print('\n📍 Creando sedes...')
    for msg in crear_sedes(): print(msg)

    print('\n👤 Creando usuario administrador...')
    for msg in crear_admin(): print(msg)

    print('\n🏢 Creando configuración de empresa...')
    for msg in crear_configuracion(): print(msg)

    print('\n💰 Creando tarifas de Retefuente 2025...')
    for msg in crear_tarifas_retefuente(): print(msg)

    print('\n🏙️  Creando tarifas de ReteICA por ciudad...')
    for msg in crear_tarifas_reteica(): print(msg)

    print('\n' + '='*55)
    print('  ✅ Setup completado')
    print('  👤 Admin: admin@erg.com')
    print('  🔑 Password: solocali')
    print('  ⚠️  Cambia la contraseña en producción')
    print('='*55 + '\n')


if __name__ == '__main__':
    main()