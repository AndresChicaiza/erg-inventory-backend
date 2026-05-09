"""
Motor de cálculo de impuestos para facturación electrónica colombiana.
Suministros Dacar S.A.S. — NIT 901.334.172-0

Reglas colombianas:
  - Retefuente: solo si cliente es agente_retenedor = True
  - ReteIVA:    solo si cliente es gran_contribuyente O (responsable_iva AND agente_retenedor)
  - ReteICA:    solo si cliente es agente_retenedor = True (empresas registradas)
                Las personas naturales NO retienen ICA aunque estén en Cali
"""
from decimal import Decimal, ROUND_HALF_UP


def _dec(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_totales_desde_items(items):
    subtotal        = _dec(0)
    descuento_total = _dec(0)
    base_iva_0      = _dec(0)
    base_iva_5      = _dec(0)
    base_iva_19     = _dec(0)
    base_excluida   = _dec(0)
    valor_iva_5     = _dec(0)
    valor_iva_19    = _dec(0)

    detalles = []

    for item in items:
        cantidad  = _dec(item.get('cantidad', 0))
        precio    = _dec(item.get('precio_unitario', 0))
        desc_pct  = _dec(100 if item.get('es_obsequio') else item.get('descuento_pct', 0))
        iva_tipo  = item.get('iva_tipo', '19')

        bruto        = cantidad * precio
        valor_desc   = _dec(bruto * desc_pct / 100)
        sub_linea    = bruto - valor_desc

        if iva_tipo == '5' and not item.get('es_obsequio'):
            iva_linea    = _dec(sub_linea * Decimal('0.05'))
            base_iva_5  += sub_linea
            valor_iva_5 += iva_linea
        elif iva_tipo == '19' and not item.get('es_obsequio'):
            iva_linea     = _dec(sub_linea * Decimal('0.19'))
            base_iva_19  += sub_linea
            valor_iva_19 += iva_linea
        elif iva_tipo == 'EXCLUIDO':
            iva_linea      = _dec(0)
            base_excluida += sub_linea
        else:
            iva_linea   = _dec(0)
            base_iva_0 += sub_linea

        total_linea      = sub_linea + iva_linea
        subtotal        += sub_linea
        descuento_total += valor_desc

        detalles.append({
            **item,
            'valor_descuento': float(valor_desc),
            'subtotal_linea':  float(sub_linea),
            'valor_iva_linea': float(iva_linea),
            'total_linea':     float(total_linea),
        })

    valor_iva_total = valor_iva_5 + valor_iva_19
    bruto_factura   = subtotal + valor_iva_total

    return {
        'detalles':        detalles,
        'subtotal':        float(subtotal),
        'descuento_total': float(descuento_total),
        'base_iva_0':      float(base_iva_0),
        'base_iva_5':      float(base_iva_5),
        'base_iva_19':     float(base_iva_19),
        'base_excluida':   float(base_excluida),
        'valor_iva_5':     float(valor_iva_5),
        'valor_iva_19':    float(valor_iva_19),
        'valor_iva_total': float(valor_iva_total),
        'bruto_factura':   float(bruto_factura),
    }


def calcular_retenciones(subtotal, valor_iva, cliente, concepto_retefuente='COMPRAS'):
    """
    Calcula retenciones según las condiciones REALES del cliente.

    Reglas:
      Retefuente → solo si cliente.agente_retenedor = True
      ReteIVA    → solo si gran_contribuyente O (responsable_iva AND agente_retenedor)
      ReteICA    → solo si cliente.agente_retenedor = True
                   (personas naturales NO retienen ICA aunque tengan ciudad)
    """
    from configuracion.models import TarifaRetefuente, TarifaReteICA

    sub = _dec(subtotal)
    iva = _dec(valor_iva)
    ret = {
        'retefuente_pct':    _dec(0),
        'valor_retefuente':  _dec(0),
        'reteiva_pct':       _dec(0),
        'valor_reteiva':     _dec(0),
        'reteica_pct':       _dec(0),
        'valor_reteica':     _dec(0),
        'total_retenciones': _dec(0),
    }

    es_agente_retenedor  = getattr(cliente, 'agente_retenedor',  False)
    es_gran_contribuyente= getattr(cliente, 'gran_contribuyente', False)
    es_responsable_iva   = getattr(cliente, 'responsable_iva',    False)

    # ── Retefuente ────────────────────────────────────────────────
    # Solo aplica si el cliente es agente retenedor (empresas registradas)
    if es_agente_retenedor:
        try:
            tarifa = TarifaRetefuente.objects.get(
                concepto=concepto_retefuente, activo=True
            )
            if sub >= _dec(tarifa.cuantia_minima):
                pct = _dec(tarifa.tarifa_porcentaje)
                ret['retefuente_pct']   = pct
                ret['valor_retefuente'] = _dec(sub * pct / 100)
        except TarifaRetefuente.DoesNotExist:
            pass

    # ── ReteIVA ───────────────────────────────────────────────────
    # Solo aplica si gran contribuyente O (responsable IVA Y agente retenedor)
    aplica_reteiva = (
        es_gran_contribuyente or
        (es_responsable_iva and es_agente_retenedor)
    )
    if aplica_reteiva and iva > 0:
        ret['reteiva_pct']   = _dec('15.00')
        ret['valor_reteiva'] = _dec(iva * Decimal('0.15'))

    # ── ReteICA ──────────────────────────────────────────────────
    # ✅ CORRECCIÓN: Solo aplica si el cliente es agente retenedor
    # Las personas naturales (CC) NO retienen ICA aunque estén en Cali
    if es_agente_retenedor:
        ciudad_cliente = getattr(cliente, 'ciudad', '') or ''
        if ciudad_cliente:
            tarifa_ica = TarifaReteICA.objects.filter(
                ciudad__iexact=ciudad_cliente, activo=True
            ).first()
            if tarifa_ica and sub > 0:
                pct_mil = _dec(tarifa_ica.tarifa_por_mil)
                ret['reteica_pct']   = pct_mil
                ret['valor_reteica'] = _dec(sub * pct_mil / 1000)

    ret['total_retenciones'] = (
        ret['valor_retefuente'] +
        ret['valor_reteiva']    +
        ret['valor_reteica']
    )

    return {k: float(v) for k, v in ret.items()}


def calcular_factura(factura):
    """Recalcula y guarda todos los totales de una instancia Factura."""
    from decimal import Decimal as D

    detalles = factura.detalles.all()
    if not detalles.exists():
        factura.subtotal = factura.total_a_pagar = D('0')
        factura.save(update_fields=[
            'subtotal','descuento_total','base_iva_0','base_iva_5','base_iva_19',
            'base_excluida','valor_iva_5','valor_iva_19','valor_iva_total',
            'retefuente_pct','valor_retefuente','reteiva_pct','valor_reteiva',
            'reteica_pct','valor_reteica','total_retenciones','total_a_pagar',
        ])
        return

    items = list(detalles.values(
        'cantidad','precio_unitario','descuento_pct','es_obsequio','iva_tipo'
    ))
    totales     = calcular_totales_desde_items(items)
    retenciones = calcular_retenciones(
        subtotal=totales['subtotal'],
        valor_iva=totales['valor_iva_total'],
        cliente=factura.cliente,
        concepto_retefuente=factura.concepto_retefuente or 'COMPRAS',
    )

    total_a_pagar = (
        _dec(totales['bruto_factura']) - _dec(retenciones['total_retenciones'])
    )

    factura.subtotal          = D(str(totales['subtotal']))
    factura.descuento_total   = D(str(totales['descuento_total']))
    factura.base_iva_0        = D(str(totales['base_iva_0']))
    factura.base_iva_5        = D(str(totales['base_iva_5']))
    factura.base_iva_19       = D(str(totales['base_iva_19']))
    factura.base_excluida     = D(str(totales['base_excluida']))
    factura.valor_iva_5       = D(str(totales['valor_iva_5']))
    factura.valor_iva_19      = D(str(totales['valor_iva_19']))
    factura.valor_iva_total   = D(str(totales['valor_iva_total']))
    factura.retefuente_pct    = D(str(retenciones['retefuente_pct']))
    factura.valor_retefuente  = D(str(retenciones['valor_retefuente']))
    factura.reteiva_pct       = D(str(retenciones['reteiva_pct']))
    factura.valor_reteiva     = D(str(retenciones['valor_reteiva']))
    factura.reteica_pct       = D(str(retenciones['reteica_pct']))
    factura.valor_reteica     = D(str(retenciones['valor_reteica']))
    factura.total_retenciones = D(str(retenciones['total_retenciones']))
    factura.total_a_pagar     = total_a_pagar

    factura.save(update_fields=[
        'subtotal','descuento_total','base_iva_0','base_iva_5','base_iva_19',
        'base_excluida','valor_iva_5','valor_iva_19','valor_iva_total',
        'retefuente_pct','valor_retefuente','reteiva_pct','valor_reteiva',
        'reteica_pct','valor_reteica','total_retenciones','total_a_pagar',
    ])