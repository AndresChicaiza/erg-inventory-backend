import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from movimientos.models import Movimiento
from bodegas.models import StockBodega
from productos.models import Producto


def predecir_agotamiento_stock(dias_historial=90):
    """
    Analiza las salidas de stock de los últimos `dias_historial` y predice 
    en cuántos días se agotará el inventario actual de cada producto.
    """
    fecha_limite = timezone.now().date() - timedelta(days=dias_historial)
    
    # 1. Obtener histórico de salidas (Movimientos tipo 'Salida')
    # Se agrupa por producto y fecha
    movimientos = Movimiento.objects.filter(
        tipo='Salida',
        fecha__gte=fecha_limite
    ).values('producto_id', 'fecha').annotate(total_salida=Sum('cantidad')).order_by('fecha')

    if not movimientos:
        return []

    # Convertir a DataFrame de Pandas
    df = pd.DataFrame(list(movimientos))
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    resultados = []

    # 2. Procesar predicción por producto
    productos_ids = df['producto_id'].unique()
    stocks_actuales = {s.producto_id: s.cantidad for s in StockBodega.objects.all()}

    for pid in productos_ids:
        # Filtrar datos del producto
        df_prod = df[df['producto_id'] == pid].copy()
        
        # Agrupar por día (para tener una serie de tiempo regular)
        df_prod = df_prod.set_index('fecha').resample('D')['total_salida'].sum().reset_index()
        df_prod['dia_idx'] = (df_prod['fecha'] - df_prod['fecha'].min()).dt.days

        if len(df_prod) < 3 or df_prod['total_salida'].sum() == 0:
            # Muy pocos datos para entrenar el modelo
            continue

        # 3. Entrenar modelo (Regresión Lineal Simple)
        X = df_prod[['dia_idx']]
        y = df_prod['total_salida']

        modelo = LinearRegression()
        modelo.fit(X, y)

        # Consumo diario promedio estimado por el modelo para "hoy" y el futuro cercano
        dia_actual_idx = (timezone.now().date() - df_prod['fecha'].min().date()).days
        consumo_diario_estimado = modelo.predict([[dia_actual_idx]])[0]

        # Evitar valores negativos irreales
        if consumo_diario_estimado <= 0:
            consumo_diario_estimado = df_prod['total_salida'].mean()  # fallback al promedio histórico

        # 4. Calcular días restantes
        stock_actual = stocks_actuales.get(pid, 0)
        
        if stock_actual <= 0:
            dias_restantes = 0
        else:
            dias_restantes = int(stock_actual / consumo_diario_estimado)

        prod = Producto.objects.get(id=pid)
        producto_nombre = prod.nombre
        codigo = prod.codigo

        # Calcular campos extra requeridos por el frontend
        riesgo = 'Bajo'
        if dias_restantes <= 5:
            riesgo = 'Alto'
        elif dias_restantes <= 15:
            riesgo = 'Medio'
            
        punto_reorden = consumo_diario_estimado * 10
        cantidad_sugerida = 0.0
        if stock_actual <= punto_reorden or stock_actual <= float(prod.stock_minimo or 0):
            cantidad_sugerida = max(0.0, (consumo_diario_estimado * 30.0) - stock_actual)
            cantidad_sugerida = round(cantidad_sugerida)

        resultados.append({
            'producto_id': pid,
            'codigo': codigo,
            'nombre': producto_nombre,
            'stock': stock_actual,
            'ventas_30_dias': df_prod['total_salida'].sum() if len(df_prod) > 0 else 0,
            'velocidad_diaria': round(consumo_diario_estimado, 3),
            'dias_restantes': dias_restantes,
            'fecha_agotamiento': (timezone.now().date() + timedelta(days=dias_restantes)).isoformat(),
            'riesgo': riesgo,
            'cantidad_sugerida_reabastecer': cantidad_sugerida,
        })

    # Ordenar por los que se agotan más rápido
    resultados = sorted(resultados, key=lambda x: x['dias_restantes'])
    
    return resultados
