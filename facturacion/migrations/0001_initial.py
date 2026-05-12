from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),
        ('productos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Factura ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id',                   models.BigAutoField(auto_created=True, primary_key=True)),
                ('numero',               models.PositiveIntegerField(unique=True, editable=False)),
                ('prefijo',              models.CharField(max_length=10, default='FACT')),
                ('numero_completo',      models.CharField(max_length=20, unique=True, editable=False)),
                ('fecha_emision',        models.DateField(default=django.utils.timezone.now)),
                ('fecha_vencimiento',    models.DateField(null=True, blank=True)),
                ('condicion_pago',       models.CharField(max_length=15, default='Contado',
                    choices=[('Contado','Contado'),('15_dias','Crédito 15 días'),
                             ('30_dias','Crédito 30 días'),('60_dias','Crédito 60 días'),
                             ('90_dias','Crédito 90 días')])),
                ('medio_pago',           models.CharField(max_length=15, default='Efectivo',
                    choices=[('Efectivo','Efectivo'),('Debito','Tarjeta Débito'),
                             ('Credito','Tarjeta Crédito'),('Transferencia','Transferencia Bancaria'),
                             ('ADDI','ADDI'),('Distecredito','Distecredito'),
                             ('Cheque','Cheque'),('Otro','Otro')])),
                ('concepto_retefuente',  models.CharField(max_length=15, default='COMPRAS', blank=True,
                    choices=[('COMPRAS','Compras generales (2.5%)'),
                             ('SERVICIOS','Servicios (4%)'),
                             ('HONORARIOS','Honorarios (11%)'),
                             ('ARRENDAMIENTO','Arrendamiento (3.5%)'),
                             ('TRANSPORTE','Transporte (1%)'),
                             ('OTROS','Otros (2.5%)')])),
                ('subtotal',             models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('descuento_total',      models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('base_iva_0',           models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('base_iva_5',           models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('base_iva_19',          models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('base_excluida',        models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('valor_iva_5',          models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('valor_iva_19',         models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('valor_iva_total',      models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('retefuente_pct',       models.DecimalField(max_digits=5,  decimal_places=2, default=0)),
                ('valor_retefuente',     models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('reteiva_pct',          models.DecimalField(max_digits=5,  decimal_places=2, default=0)),
                ('valor_reteiva',        models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('reteica_pct',          models.DecimalField(max_digits=8,  decimal_places=3, default=0)),
                ('valor_reteica',        models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('total_retenciones',    models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('total_a_pagar',        models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('estado',               models.CharField(max_length=10, default='Borrador',
                    choices=[('Borrador','Borrador'),('Emitida','Emitida'),
                             ('Pagada','Pagada'),('Vencida','Vencida'),('Anulada','Anulada')])),
                ('notas',                models.TextField(blank=True)),
                ('cufe',                 models.CharField(max_length=200, blank=True)),
                ('qr_url',               models.TextField(blank=True)),
                ('fecha_emision_ts',     models.DateTimeField(null=True, blank=True)),
                ('creado_en',            models.DateTimeField(auto_now_add=True)),
                ('actualizado_en',       models.DateTimeField(auto_now=True)),
                ('cliente',              models.ForeignKey(
                                             on_delete=django.db.models.deletion.PROTECT,
                                             related_name='facturas',
                                             to='clientes.cliente')),
                ('creado_por',           models.ForeignKey(
                                             null=True,
                                             on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='facturas_creadas',
                                             to=settings.AUTH_USER_MODEL)),
                ('emitida_por',          models.ForeignKey(
                                             null=True, blank=True,
                                             on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='facturas_emitidas',
                                             to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'facturas', 'ordering': ['-numero'], 'verbose_name': 'Factura'},
        ),

        # ── DetalleFactura ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='DetalleFactura',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True)),
                ('descripcion',     models.CharField(max_length=300)),
                ('cantidad',        models.DecimalField(max_digits=12, decimal_places=3)),
                ('precio_unitario', models.DecimalField(max_digits=14, decimal_places=2)),
                ('descuento_pct',   models.DecimalField(max_digits=5,  decimal_places=2, default=0)),
                ('es_obsequio',     models.BooleanField(default=False)),
                ('iva_tipo',        models.CharField(max_length=10, default='19',
                    choices=[('0','Exento (0%)'),('5','IVA 5%'),
                             ('19','IVA 19%'),('EXCLUIDO','Excluido de IVA')])),
                ('valor_descuento', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('subtotal_linea',  models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('valor_iva_linea', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('total_linea',     models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('orden',           models.PositiveIntegerField(default=0)),
                ('factura',         models.ForeignKey(
                                        on_delete=django.db.models.deletion.CASCADE,
                                        related_name='detalles',
                                        to='facturacion.factura')),
                ('producto',        models.ForeignKey(
                                        null=True, blank=True,
                                        on_delete=django.db.models.deletion.SET_NULL,
                                        related_name='detalles_factura',
                                        to='productos.producto')),
            ],
            options={'db_table': 'factura_detalles', 'ordering': ['orden', 'id']},
        ),

        # ── NotaCredito ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='NotaCredito',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True)),
                ('numero',           models.PositiveIntegerField(unique=True, editable=False)),
                ('numero_completo',  models.CharField(max_length=20, unique=True, editable=False)),
                ('motivo',           models.CharField(max_length=15,
                    choices=[('DEVOLUCION','Devolución de mercancía'),
                             ('DESCUENTO','Descuento comercial'),
                             ('ANULACION','Anulación de factura'),
                             ('PRECIO','Ajuste de precio'),
                             ('OTRO','Otro')])),
                ('descripcion',      models.TextField()),
                ('subtotal',         models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('valor_iva',        models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('total',            models.DecimalField(max_digits=16, decimal_places=2, default=0)),
                ('creado_en',        models.DateTimeField(auto_now_add=True)),
                ('factura_original', models.ForeignKey(
                                         on_delete=django.db.models.deletion.PROTECT,
                                         related_name='notas_credito',
                                         to='facturacion.factura')),
                ('creado_por',       models.ForeignKey(
                                         null=True,
                                         on_delete=django.db.models.deletion.SET_NULL,
                                         to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'notas_credito', 'ordering': ['-creado_en'], 'verbose_name': 'Nota Crédito'},
        ),
    ]