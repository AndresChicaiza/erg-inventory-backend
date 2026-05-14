from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrReadOnly, CanCreateCliente
from .models import Cliente
from .serializers import ClienteSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import openpyxl


class ClienteListCreateView(generics.ListCreateAPIView):
    queryset           = Cliente.objects.all()
    serializer_class   = ClienteSerializer
    permission_classes = [CanCreateCliente]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    # ✅ Fix: campos correctos del modelo nuevo
    search_fields      = ['razon_social', 'numero_documento', 'email', 'ciudad', 'nombre_comercial']
    ordering_fields    = ['razon_social', 'tipo_documento', 'estado', 'ciudad']

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)


class ClienteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Cliente.objects.all()
    serializer_class   = ClienteSerializer
    permission_classes = [CanCreateCliente]

class ClienteImportView(APIView):
    """POST /api/clientes/importar/"""
    permission_classes = [IsAdminOrReadOnly]
    
    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wb = openpyxl.load_workbook(archivo, data_only=True)
            sheet = wb.active
            creados = 0
            
            for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
                if i == 1: continue
                if not row[0]: continue
                
                num_doc = str(row[0]).strip()
                razon = str(row[1]).strip() if row[1] else ''
                email = str(row[2]).strip() if row[2] else ''
                ciudad = str(row[3]).strip() if row[3] else ''
                
                if not razon: continue
                
                _, created = Cliente.objects.update_or_create(
                    numero_documento=num_doc,
                    defaults={
                        'razon_social': razon,
                        'email': email,
                        'ciudad': ciudad,
                        'tipo_documento': 'NIT',
                    }
                )
                if created: creados += 1
                
            return Response({'mensaje': f'Importación exitosa. Creados: {creados}'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)