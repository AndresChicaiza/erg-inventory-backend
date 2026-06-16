from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.http import HttpResponse
from django.db.models import Sum
from .models import CuentaPorCobrar
from clientes.models import Cliente
import openpyxl

class Exogena1008View(APIView):
    """
    Exportación de Cuentas por Cobrar (Formato 1008 DIAN).
    Reporta los saldos a favor agrupados por cliente.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. Traer solo cuentas con saldo a favor
        cxc_pendientes = CuentaPorCobrar.objects.filter(estado__in=['Pendiente', 'Parcial', 'Vencida'])
        saldos_por_cliente = cxc_pendientes.values('cliente').annotate(saldo_total=Sum('saldo'))

        # 2. Crear Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Formato 1008 - DIAN"

        # Cabeceras estándar DIAN
        headers = [
            'Concepto', 'Tipo Documento', 'Número Identificación', 'DV',
            'Primer Apellido', 'Segundo Apellido', 'Primer Nombre', 'Otros Nombres',
            'Razón Social', 'Dirección', 'Código Dpto', 'Código Mun', 'País', 'Saldo CXC'
        ]
        ws.append(headers)

        # 3. Llenar filas
        for row in saldos_por_cliente:
            cliente = Cliente.objects.get(id=row['cliente'])
            saldo = row['saldo_total']
            
            # Mapeo básico de Tipo Documento a Código DIAN (13=CC, 31=NIT, 22=CE)
            tipo_dian = '13'
            if cliente.tipo_documento == 'NIT': tipo_dian = '31'
            elif cliente.tipo_documento == 'CE': tipo_dian = '22'
            elif cliente.tipo_documento == 'PASAPORTE': tipo_dian = '41'
            
            ws.append([
                '1315', # Concepto genérico Cuentas por Cobrar Clientes
                tipo_dian,
                cliente.numero_documento,
                cliente.digito_verificacion,
                cliente.exogena_primer_apellido,
                cliente.exogena_segundo_apellido,
                cliente.exogena_primer_nombre,
                cliente.exogena_segundo_nombre,
                cliente.exogena_razon_social,
                cliente.direccion,
                '76',  # Dpto Valle del Cauca (por defecto para este ERP demo)
                '001', # Cali
                '169', # Colombia
                float(saldo)
            ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=formato_1008_cxc_exogena.xlsx'
        wb.save(response)
        return response
