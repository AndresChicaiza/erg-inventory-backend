from django.db import migrations, models
import django.db.models.deletion
import secrets


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('productos',    '0006_stock_decimal'),
        ('clientes',     '__first__'),
        ('facturacion',  '__first__'),
        ('users',        '__first__'),
    ]

    operations = [
        # ── CatalogoPublico ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='CatalogoPublico',
            fields=[
                ('id',                  models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('producto',            models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='catalogo_publico', to='productos.producto')),
                ('visible',             models.BooleanField(default=False, help_text='Si está activo, el producto aparece en el portal B2B.')),
                ('descripcion_publica', models.TextField(blank=True)),
                ('precio_publico',      models.DecimalField(decimal_places=2, max_digits=14)),
                ('imagen_publica',      models.ImageField(blank=True, null=True, upload_to='marketplace/')),
                ('categoria_display',   models.CharField(blank=True, max_length=100)),
                ('stock_maximo_pedido', models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ('orden',               models.IntegerField(default=0)),
                ('creado_en',           models.DateTimeField(auto_now_add=True)),
                ('actualizado_en',      models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Ítem de Catálogo',
                'db_table':     'marketplace_catalogo',
                'ordering':     ['orden', 'producto__nombre'],
            },
        ),

        # ── PedidoOnline ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='PedidoOnline',
            fields=[
                ('id',                models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token',             models.CharField(editable=False, max_length=64, unique=True)),
                ('cliente_nit',       models.CharField(blank=True, max_length=30)),
                ('cliente_nombre',    models.CharField(max_length=250)),
                ('cliente_email',     models.EmailField()),
                ('cliente_telefono',  models.CharField(blank=True, max_length=25)),
                ('cliente_ciudad',    models.CharField(blank=True, max_length=100)),
                ('cliente_direccion', models.TextField(blank=True)),
                ('notas',             models.TextField(blank=True)),
                ('subtotal',          models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('total',             models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('estado',            models.CharField(
                    choices=[('Pendiente','Pendiente — por revisar'),('En_Revision','En Revisión'),('Aprobado','Aprobado → Factura creada'),('Rechazado','Rechazado')],
                    default='Pendiente', max_length=15
                )),
                ('motivo_rechazo',    models.TextField(blank=True)),
                ('revisado_en',       models.DateTimeField(blank=True, null=True)),
                ('creado_en',         models.DateTimeField(auto_now_add=True)),
                ('actualizado_en',    models.DateTimeField(auto_now=True)),
                ('cliente_erp',       models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos_online', to='clientes.cliente')),
                ('factura',           models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedido_online_origen', to='facturacion.factura')),
                ('revisado_por',      models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos_revisados', to='users.usuario')),
            ],
            options={
                'verbose_name': 'Pedido Online',
                'db_table':     'marketplace_pedidos',
                'ordering':     ['-creado_en'],
            },
        ),

        # ── DetallePedidoOnline ──────────────────────────────────────────────
        migrations.CreateModel(
            name='DetallePedidoOnline',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_producto', models.CharField(max_length=200)),
                ('cantidad',        models.DecimalField(decimal_places=3, max_digits=12)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=14)),
                ('subtotal_linea',  models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('catalogo_item',   models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='marketplace.catalogopublico')),
                ('pedido',          models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='marketplace.pedidoonline')),
                ('producto',        models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='productos.producto')),
            ],
            options={
                'db_table': 'marketplace_detalles',
            },
        ),
    ]
