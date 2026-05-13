import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from clientes.models import Cliente
from facturacion.models import Factura, DetalleFactura
from productos.models import Producto
from cxc.models import CuentaPorCobrar
from bodegas.models import Bodega

User = get_user_model()
user = User.objects.first()
cliente = Cliente.objects.first()
producto = Producto.objects.first()
bodega = Bodega.objects.first()

print(f"Probando con cliente: {cliente} y producto: {producto}")

# Crear factura de prueba a crédito 30 días
factura = Factura.objects.create(
    cliente=cliente,
    vendedor=user,
    bodega=bodega,
    condicion_pago='30_dias',
    estado='Borrador'
)

DetalleFactura.objects.create(
    factura=factura,
    producto=producto,
    descripcion=producto.nombre,
    cantidad=1,
    precio_unitario=1000,
    iva_tipo='19'
)

factura.recalcular_totales()
print(f"Factura subtotal: {factura.subtotal}, total: {factura.total_a_pagar}")

# Emitir factura simulando la vista
from rest_framework.test import APIRequestFactory
from facturacion.views import EmitirFacturaView
from rest_framework.request import Request

factory = APIRequestFactory()
request = factory.post(f'/api/facturas/{factura.id}/emitir/')
request.user = user

view = EmitirFacturaView.as_view()
response = view(request, pk=factura.id)
print(f"Respuesta emisión: {response.status_code} - {response.data}")

if response.status_code == 200:
    factura.refresh_from_db()
    print(f"Estado Factura tras emitir: {factura.estado}")
    cxc = CuentaPorCobrar.objects.filter(factura=factura).first()
    if cxc:
        print(f"CXC Creada Exitosamente: {cxc.id} | Monto: {cxc.monto_total} | Estado: {cxc.estado}")
        
        # Simular pago total
        cxc.monto_pagado = cxc.monto_total
        cxc.save()
        cxc.refresh_from_db()
        print(f"Estado CXC tras pago: {cxc.estado}")
        
        factura.refresh_from_db()
        print(f"Estado Factura tras pago de CXC: {factura.estado}")
    else:
        print("ERROR: No se creó CXC")
