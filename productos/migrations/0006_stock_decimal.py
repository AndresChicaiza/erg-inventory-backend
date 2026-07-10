# Generated manually — stock/stock_minimo: IntegerField → DecimalField(14, 3)
# Permite fracciones en unidades como KG, LT, MT, etc.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0005_lote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='stock',
            field=models.DecimalField(
                decimal_places=3,
                default=0,
                max_digits=14,
                help_text='Cantidad disponible. Acepta decimales para unidades como KG, LT, MT.'
            ),
        ),
        migrations.AlterField(
            model_name='producto',
            name='stock_minimo',
            field=models.DecimalField(
                decimal_places=3,
                default=5,
                max_digits=14,
                help_text='Stock mínimo de alerta. Acepta decimales.'
            ),
        ),
        # También ajustamos el campo en la tabla de lotes
        migrations.AlterField(
            model_name='lote',
            name='stock_disponible',
            field=models.DecimalField(
                decimal_places=3,
                default=0,
                max_digits=14,
            ),
        ),
    ]
