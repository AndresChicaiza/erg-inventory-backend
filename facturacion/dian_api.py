"""
facturacion/dian_api.py
────────────────────────────────────────────────────────────────────────────────
Módulo puente para Facturación Electrónica ante la DIAN (Colombia).

Modo actual: SIMULADOR LOCAL (para desarrollo y pruebas de estudio).
Cuando se decida un Proveedor Tecnológico real, se reemplaza la clase
`DianSimulador` por `DianProveedorReal` y todo el flujo sigue igual.
────────────────────────────────────────────────────────────────────────────────
"""
import hashlib
import uuid
import json
from datetime import datetime
from decimal import Decimal
from django.conf import settings


class DecimalEncoder(json.JSONEncoder):
    """Encoder para serializar Decimal a JSON."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# ── Mapeos DIAN ──────────────────────────────────────────────────────────────

TIPO_DOC_DIAN = {
    'CC': '13', 'NIT': '31', 'CE': '22',
    'PASAPORTE': '41', 'NIT_EXTRAN': '42', 'RUT': '31',
}

MEDIO_PAGO_DIAN = {
    'Efectivo': '10', 'Debito': '49', 'Credito': '48',
    'Transferencia': '47', 'Cheque': '20', 'ADDI': '99',
    'Distecredito': '99', 'Otro': '99',
}

TIPO_IVA_DIAN = {
    '0': {'codigo': '01', 'porcentaje': 0},
    '5': {'codigo': '01', 'porcentaje': 5},
    '19': {'codigo': '01', 'porcentaje': 19},
    'EXCLUIDO': {'codigo': '04', 'porcentaje': 0},
}


def generar_cufe(factura, config):
    """
    Genera un CUFE (Código Único de Factura Electrónica) simulado.
    En producción, este cálculo sigue el Anexo Técnico DIAN v1.9+
    usando SHA-384 sobre los campos obligatorios.
    """
    cadena = (
        f"{factura.numero_completo}"
        f"{factura.fecha_emision.isoformat()}"
        f"{float(factura.subtotal):.2f}"
        f"01"  # Código IVA
        f"{float(factura.valor_iva_total):.2f}"
        f"04"  # Código IC
        f"0.00"  # ICA (simplificado)
        f"{float(factura.total_a_pagar):.2f}"
        f"{config.nit}"
        f"{factura.cliente.numero_documento}"
        # En producción: + clave técnica DIAN + ambiente
    )
    return hashlib.sha384(cadena.encode()).hexdigest()


def construir_xml_ubl(factura, config):
    """
    Construye la estructura del documento electrónico en formato UBL 2.1.
    Retorna un diccionario que representa la estructura XML.
    En producción con Proveedor Tecnológico, este JSON se envía a su API.
    """
    detalles = factura.detalles.select_related('producto').all()

    documento = {
        'numero': factura.numero_completo,
        'prefijo': factura.prefijo,
        'consecutivo': factura.numero,
        'fecha_emision': factura.fecha_emision.isoformat(),
        'hora_emision': datetime.now().strftime('%H:%M:%S-05:00'),
        'fecha_vencimiento': factura.fecha_vencimiento.isoformat() if factura.fecha_vencimiento else None,
        'tipo_documento': '01',  # 01=Factura, 91=NC, 92=ND
        'moneda': 'COP',

        # Emisor (tu empresa)
        'emisor': {
            'tipo_documento': '31',  # NIT
            'numero_documento': config.nit,
            'dv': config.digito_verificacion,
            'razon_social': config.razon_social,
            'nombre_comercial': config.nombre_comercial,
            'direccion': config.direccion,
            'ciudad': config.ciudad,
            'departamento': config.departamento,
            'pais': 'CO',
            'codigo_pais': '169',
            'telefono': config.telefono,
            'email': config.email,
            'regimen': config.regimen,
            'responsabilidades': config.responsabilidades,
        },

        # Receptor (cliente)
        'receptor': {
            'tipo_documento': TIPO_DOC_DIAN.get(factura.cliente.tipo_documento, '13'),
            'numero_documento': factura.cliente.numero_documento,
            'dv': factura.cliente.digito_verificacion,
            'razon_social': factura.cliente.razon_social,
            'direccion': factura.cliente.direccion,
            'ciudad': factura.cliente.ciudad,
            'departamento': factura.cliente.departamento,
            'pais': 'CO',
            'email': factura.cliente.email,
            'regimen': factura.cliente.get_regimen_tributario_display()
                       if hasattr(factura.cliente, 'get_regimen_tributario_display') else '',
        },

        # Medio de pago
        'medio_pago': {
            'codigo': MEDIO_PAGO_DIAN.get(factura.medio_pago, '99'),
            'forma_pago': '1' if factura.condicion_pago == 'Contado' else '2',
        },

        # Totales
        'totales': {
            'subtotal': float(factura.subtotal),
            'descuento_total': float(factura.descuento_total),
            'base_iva_0': float(factura.base_iva_0),
            'base_iva_5': float(factura.base_iva_5),
            'base_iva_19': float(factura.base_iva_19),
            'base_excluida': float(factura.base_excluida),
            'valor_iva_5': float(factura.valor_iva_5),
            'valor_iva_19': float(factura.valor_iva_19),
            'valor_iva_total': float(factura.valor_iva_total),
            'retefuente': float(factura.valor_retefuente),
            'reteiva': float(factura.valor_reteiva),
            'reteica': float(factura.valor_reteica),
            'total_retenciones': float(factura.total_retenciones),
            'total_a_pagar': float(factura.total_a_pagar),
        },

        # Líneas de detalle
        'lineas': [
            {
                'numero_linea': i + 1,
                'codigo_producto': d.producto.codigo if d.producto else '',
                'descripcion': d.descripcion,
                'cantidad': float(d.cantidad),
                'unidad': 'NIU',  # Unidad estándar DIAN
                'precio_unitario': float(d.precio_unitario),
                'descuento_porcentaje': float(d.descuento_pct),
                'descuento_valor': float(d.valor_descuento),
                'subtotal_linea': float(d.subtotal_linea),
                'iva_tipo': TIPO_IVA_DIAN.get(d.iva_tipo, {'codigo': '01', 'porcentaje': 0}),
                'valor_iva': float(d.valor_iva_linea),
                'total_linea': float(d.total_linea),
                'es_obsequio': d.es_obsequio,
            }
            for i, d in enumerate(detalles)
        ],
    }

    return documento


class DianSimulador:
    """
    Simulador local de Facturación Electrónica DIAN.
    Genera CUFE, QR y respuestas como si fuera un Proveedor Tecnológico real.
    Útil para desarrollo, pruebas de estudio y demostraciones.
    """

    @staticmethod
    def emitir(factura):
        """
        Simula el envío de una factura electrónica a la DIAN.
        Retorna un dict con: cufe, qr_url, xml_base64, estado_dian, mensajes.
        """
        from configuracion.models import ConfiguracionEmpresa
        config = ConfiguracionEmpresa.objects.first()

        if not config:
            return {
                'exito': False,
                'estado_dian': 'ERROR',
                'mensajes': ['No se ha configurado la empresa. Vaya a Configuración.'],
            }

        # 1. Construir documento UBL
        documento_ubl = construir_xml_ubl(factura, config)

        # 2. Generar CUFE
        cufe = generar_cufe(factura, config)

        # 3. Generar URL de QR (en producción apunta al portal DIAN)
        qr_url = (
            f"https://catalogo-vpfe.dian.gov.co/document/searchqr?"
            f"documentkey={cufe}"
        )

        # 4. Simular respuesta exitosa de la DIAN
        tracking_id = str(uuid.uuid4())[:8].upper()

        return {
            'exito': True,
            'cufe': cufe,
            'qr_url': qr_url,
            'estado_dian': 'ACEPTADA',
            'tracking_id': f'DIAN-{tracking_id}',
            'fecha_validacion': datetime.now().isoformat(),
            'documento_ubl': documento_ubl,
            'mensajes': [
                'Documento validado exitosamente por la DIAN (simulación).',
                f'CUFE asignado: {cufe[:20]}...',
            ],
            'xml_base64': None,  # En producción: el XML firmado en base64
        }

    @staticmethod
    def consultar_estado(cufe):
        """Simula consulta de estado de un documento ya enviado."""
        if not cufe:
            return {'estado': 'NO_ENVIADA', 'mensaje': 'Factura no ha sido enviada a la DIAN'}

        return {
            'estado': 'ACEPTADA',
            'cufe': cufe,
            'fecha_validacion': datetime.now().isoformat(),
            'mensaje': 'Documento aceptado por la DIAN (simulación)',
        }

    @staticmethod
    def emitir_nota_credito(nota_credito):
        """Simula el envío de una Nota de Crédito electrónica."""
        cufe_nc = hashlib.sha384(
            f"NC-{nota_credito.numero_completo}-{datetime.now().isoformat()}".encode()
        ).hexdigest()

        return {
            'exito': True,
            'cufe': cufe_nc,
            'estado_dian': 'ACEPTADA',
            'tipo_documento': '91',  # 91 = Nota Crédito
            'mensajes': ['Nota de Crédito validada exitosamente (simulación).'],
        }


# ── Instancia activa ─────────────────────────────────────────────────────────
# Cambiar a DianProveedorReal cuando se integre un proveedor tecnológico
dian_service = DianSimulador()
