from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Agrega el campo 'bodega' (FK opcional) al modelo Venta.
    Esto permite registrar desde qué bodega salió el producto en cada venta.
    """

    dependencies = [
        ('ventas', '0001_initial'),
        ('bodegas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='bodega',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='ventas',
                to='bodegas.bodega',
                verbose_name='Bodega de salida',
            ),
        ),
    ]