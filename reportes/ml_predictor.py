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

        producto_nombre = Producto.objects.get(id=pid).nombre

        resultados.append({
            'producto_id': pid,
            'producto_nombre': producto_nombre,
            'stock_actual': stock_actual,
            'consumo_diario_estimado': round(consumo_diario_estimado, 2),
            'dias_para_agotarse': dias_restantes,
            'fecha_estimada_agotamiento': (timezone.now().date() + timedelta(days=dias_restantes)).isoformat()
        })

    # Ordenar por los que se agotan más rápido
    resultados = sorted(resultados, key=lambda x: x['dias_para_agotarse'])
    
    return resultados
