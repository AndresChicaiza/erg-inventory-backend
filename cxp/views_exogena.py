from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.http import HttpResponse
from django.db.models import Sum
from .models import CuentaPorPagar
from proveedores.models import Proveedor
import openpyxl

class Exogena1009View(APIView):
    """
    Exportación de Cuentas por Pagar (Formato 1009 DIAN).
    Reporta los pasivos (deudas) agrupados por proveedor.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. Traer deudas pendientes
        cxp_pendientes = CuentaPorPagar.objects.filter(estado__in=['Pendiente', 'Parcial', 'Vencida'])
        saldos_por_prov = cxp_pendientes.values('proveedor').annotate(saldo_total=Sum('saldo'))

        # 2. Crear Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Formato 1009 - DIAN"

        headers = [
            'Concepto', 'Tipo Documento', 'Número Identificación', 'DV',
            'Primer Apellido', 'Segundo Apellido', 'Primer Nombre', 'Otros Nombres',
            'Razón Social', 'Dirección', 'Código Dpto', 'Código Mun', 'País', 'Saldo CXP'
        ]
        ws.append(headers)

        # 3. Llenar filas
        for row in saldos_por_prov:
            prov = Proveedor.objects.get(id=row['proveedor'])
            saldo = row['saldo_total']
            
            tipo_dian = '13'
            if prov.tipo_documento == 'NIT': tipo_dian = '31'
            elif prov.tipo_documento == 'CE': tipo_dian = '22'
            elif prov.tipo_documento == 'PASAPORTE': tipo_dian = '41'
            
            ws.append([
                '2205', # Concepto Proveedores Nacionales
                tipo_dian,
                prov.numero_documento,
                prov.digito_verificacion,
                prov.exogena_primer_apellido,
                prov.exogena_segundo_apellido,
                prov.exogena_primer_nombre,
                prov.exogena_segundo_nombre,
                prov.exogena_razon_social,
                prov.direccion,
                '76',
                '001',
                '169',
                float(saldo)
            ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=formato_1009_cxp_exogena.xlsx'
        wb.save(response)
        return response
