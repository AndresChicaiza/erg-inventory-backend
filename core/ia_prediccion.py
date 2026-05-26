from django.utils import timezone
from django.db.models import Sum
from productos.models import Producto
from facturacion.models import DetalleFactura

def calcular_predicciones_demanda():
    hoy = timezone.now().date()
    hace_30_dias = hoy - timezone.timedelta(days=30)
    
    # 1. Obtener ventas por producto en los últimos 30 días
    ventas = DetalleFactura.objects.filter(
        factura__estado__in=['Emitida', 'Pagada', 'Vencida'],
        factura__fecha_emision__gte=hace_30_dias
    ).values('producto_id').annotate(
        total_vendido=Sum('cantidad')
    )
    
    ventas_dict = {item['producto_id']: float(item['total_vendido']) for item in ventas}
    
    predicciones = []
    
    # 2. Recorrer productos y estimar agotamiento
    productos = Producto.objects.all()
    for prod in productos:
        if not prod.id:
            continue
            
        stock_actual = float(prod.stock) if prod.stock else 0.0
        total_30_dias = ventas_dict.get(prod.id, 0.0)
        
        # Velocidad diaria (unidades / día)
        velocidad_diaria = total_30_dias / 30.0
        
        if velocidad_diaria > 0:
            dias_restantes = stock_actual / velocidad_diaria
            pronostico_fecha = (timezone.now() + timezone.timedelta(days=dias_restantes)).date()
            dias_restantes_int = int(round(dias_restantes))
        else:
            dias_restantes_int = 999  # Sin riesgo inmediato de agotarse
            pronostico_fecha = None
            
        # Riesgo
        riesgo = 'Bajo'
        if dias_restantes_int <= 5:
            riesgo = 'Alto'
        elif dias_restantes_int <= 15:
            riesgo = 'Medio'
            
        # Sugerir reabastecimiento si stock actual es menor a 10 días de venta o menor a stock mínimo
        punto_reorden = velocidad_diaria * 10
        cantidad_sugerida = 0.0
        
        if stock_actual <= punto_reorden or stock_actual <= float(prod.stock_minimo or 0):
            cantidad_sugerida = max(0.0, (velocidad_diaria * 30.0) - stock_actual)
            cantidad_sugerida = round(cantidad_sugerida)
            
        predicciones.append({
            'producto_id': prod.id,
            'codigo': prod.codigo,
            'nombre': prod.nombre,
            'stock': stock_actual,
            'ventas_30_dias': total_30_dias,
            'velocidad_diaria': round(velocidad_diaria, 3),
            'dias_restantes': dias_restantes_int,
            'fecha_agotamiento': str(pronostico_fecha) if pronostico_fecha else 'N/A',
            'riesgo': riesgo,
            'cantidad_sugerida_reabastecer': cantidad_sugerida,
        })
        
    # Ordenar: menor cantidad de días restantes primero (excluyendo aquellos sin ventas en absoluto)
    predicciones.sort(key=lambda x: (x['dias_restantes'] if x['velocidad_diaria'] > 0 else 9999))
    return predicciones
