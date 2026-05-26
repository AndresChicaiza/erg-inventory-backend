import os
import json
from google import genai
from google.genai import types
from django.db.models import Sum, Q, F
from django.utils import timezone
from productos.models import Producto
from facturacion.models import Factura
from cxc.models import CuentaPorCobrar
from cxp.models import CuentaPorPagar

# Configuración Gemini
api_key = os.environ.get('GEMINI_API_KEY', '')


def _get_client():
    return genai.Client(api_key=api_key)


def get_intent_gemini(query_text):
    prompt = (
        f'Eres el cerebro de un ERP. El usuario dice: "{query_text}". '
        'Clasifica la intención en un JSON con las llaves "intent" y "keywords". '
        'Intents posibles: ventas, cxc, cxp, inventario_alerta, inventario, ayuda. '
        'Si la intención es "inventario" y busca algo específico, pon los términos en "keywords", si no déjalo vacío. '
        'Responde SOLO el JSON crudo sin bloques de código markdown.'
    )
    try:
        client = _get_client()
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res)
    except Exception as e:
        print("Error en get_intent:", e)
        return {'intent': 'ayuda', 'keywords': []}


def format_response_gemini(query_text, intent, datos_raw):
    prompt = (
        'Eres un Asistente Inteligente de un ERP. Responde la consulta del usuario '
        'basándote EXCLUSIVAMENTE en los datos de la base de datos provistos. '
        f'Usuario: "{query_text}". '
        f'Contexto de Base de Datos: {json.dumps(datos_raw, default=str)}. '
        'Reglas: Sé amable, conciso y profesional. '
        'Utiliza formato Markdown con negritas para resaltar números importantes. '
        'No inventes datos. Si el contexto de BD está vacío, di que no encontraste información.'
    )
    try:
        client = _get_client()
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Ocurrió un error al conectar con Gemini: {str(e)}"


def responder_consulta_ia(query_text):
    query_text = query_text.strip()

    # Si no hay API key configurada, retornar un error amigable
    if not api_key or api_key == 'tu_clave_de_google_ai_studio_aqui':
        return {
            'respuesta': "⚠️ La API de Gemini no está configurada. Por favor, añade `GEMINI_API_KEY` a tu archivo `.env` del backend.",
            'datos': [],
            'tipo': 'ayuda'
        }

    # 1. Obtener la intención con Gemini
    analisis = get_intent_gemini(query_text)
    intent = analisis.get('intent', 'ayuda')
    keywords = analisis.get('keywords', [])

    datos = []
    datos_resumen = {}

    hoy = timezone.now().date()

    # 2. Consultar la Base de Datos según la intención
    if intent == 'ventas':
        ventas = Factura.objects.exclude(estado='Anulada').filter(
            fecha_emision__year=hoy.year, fecha_emision__month=hoy.month
        )
        total = ventas.aggregate(t=Sum('total_a_pagar'))['t'] or 0
        cant = ventas.count()
        datos = list(ventas.values('numero_completo', 'cliente__razon_social', 'total_a_pagar', 'estado')[:10])
        datos_resumen = {'total_facturas_mes': cant, 'valor_total_mes': float(total), 'facturas_recientes': datos}

    elif intent == 'cxc':
        cxc = CuentaPorCobrar.objects.filter(estado__in=['Pendiente', 'Parcial', 'Vencida'])
        total = cxc.aggregate(t=Sum('saldo'))['t'] or 0
        datos = list(cxc.values('cliente__razon_social', 'concepto', 'saldo', 'fecha_vencimiento')[:10])
        datos_resumen = {'cuentas_pendientes': cxc.count(), 'saldo_total_adeudado': float(total), 'top_deudores': datos}

    elif intent == 'cxp':
        cxp = CuentaPorPagar.objects.filter(estado__in=['Pendiente', 'Parcial', 'Vencida'])
        total = cxp.aggregate(t=Sum('saldo'))['t'] or 0
        datos = list(cxp.values('proveedor__razon_social', 'concepto', 'saldo', 'fecha_vencimiento')[:10])
        datos_resumen = {'cuentas_por_pagar': cxp.count(), 'saldo_total_deuda': float(total), 'top_proveedores': datos}

    elif intent == 'inventario_alerta':
        stock_bajo = Producto.objects.filter(stock__lte=F('stock_minimo'))
        datos = list(stock_bajo.values('codigo', 'nombre', 'stock', 'stock_minimo')[:15])
        datos_resumen = {'cantidad_productos_alerta': stock_bajo.count(), 'productos': datos}

    elif intent == 'inventario':
        if keywords:
            search_query = Q()
            for kw in keywords:
                search_query |= Q(nombre__icontains=kw) | Q(codigo__icontains=kw)
            prods = Producto.objects.filter(search_query)
        else:
            prods = Producto.objects.all()

        datos = list(prods.order_by('-stock').values('codigo', 'nombre', 'stock', 'precio_venta')[:10])
        datos_resumen = {'total_productos_encontrados': prods.count(), 'productos': datos}

    else:
        intent = 'ayuda'
        datos_resumen = {'info': 'El usuario necesita ayuda o hizo una pregunta fuera del alcance del ERP.'}

    # 3. Formular la respuesta en lenguaje natural usando Gemini
    respuesta_final = format_response_gemini(query_text, intent, datos_resumen)

    return {
        'respuesta': respuesta_final,
        'datos': datos,
        'tipo': intent
    }
