from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='iva_tipo',
            field=models.CharField(
                max_length=10,
                default='19',
                choices=[
                    ('19',       'IVA 19%'),
                    ('5',        'IVA 5%'),
                    ('0',        'Exento (0%)'),
                    ('EXCLUIDO', 'Excluido de IVA'),
                ],
                help_text='Tipo de IVA que aplica a este producto',
            ),
        ),
        migrations.AddField(
            model_name='producto',
            name='iva_incluido',
            field=models.BooleanField(
                default=False,
                help_text='Si el precio de venta ya incluye el IVA',
            ),
        ),
        migrations.AddField(
            model_name='producto',
            name='unidad_medida',
            field=models.CharField(
                max_length=10,
                default='UND',
                choices=[
                    ('UND',  'Unidades'),
                    ('KG',   'Kilogramos'),
                    ('GR',   'Gramos'),
                    ('LT',   'Litros'),
                    ('ML',   'Mililitros'),
                    ('MT',   'Metros'),
                    ('MT2',  'Metros cuadrados'),
                    ('MT3',  'Metros cúbicos'),
                    ('ROLLO','Rollos'),
                    ('CJA',  'Cajas'),
                    ('BLS',  'Bolsas'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='producto',
            name='tipo_inventario',
            field=models.CharField(
                max_length=15,
                default='TERMINADO',
                choices=[
                    ('TERMINADO',    'Producto Terminado'),
                    ('MATERIA_PRIMA','Materia Prima'),
                    ('TIENDA',       'Producto de Tienda'),
                ],
            ),
        ),
    ]