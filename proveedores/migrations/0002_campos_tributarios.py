from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Actualiza Proveedor con campos tributarios DIAN.
    """

    dependencies = [
        ('proveedores', '0001_initial'),
        ('users', '0002_sede_y_roles'),
    ]

    operations = [
        migrations.RemoveField(model_name='proveedor', name='empresa'),
        migrations.RemoveField(model_name='proveedor', name='tipo'),

        migrations.AddField(
            model_name='proveedor', name='tipo_documento',
            field=models.CharField(max_length=12, default='NIT',
                choices=[('NIT','NIT'),('CC','Cédula de Ciudadanía'),
                         ('CE','Cédula de Extranjería'),('PASAPORTE','Pasaporte'),
                         ('NIT_EXTRAN','NIT Extranjero')]),
        ),
        migrations.AddField(
            model_name='proveedor', name='numero_documento',
            field=models.CharField(max_length=20, unique=True, default='000'),
            preserve_default=False,
        ),
        migrations.AddField(model_name='proveedor', name='digito_verificacion', field=models.CharField(max_length=1, blank=True)),
        migrations.AddField(model_name='proveedor', name='razon_social',        field=models.CharField(max_length=250, default=''), preserve_default=False),
        migrations.AddField(model_name='proveedor', name='nombre_comercial',    field=models.CharField(max_length=250, blank=True)),
        migrations.AddField(model_name='proveedor', name='telefono2',           field=models.CharField(max_length=25, blank=True)),
        migrations.AddField(model_name='proveedor', name='departamento',        field=models.CharField(max_length=100, blank=True)),
        migrations.AddField(model_name='proveedor', name='pais',                field=models.CharField(max_length=100, default='Colombia')),
        migrations.AddField(
            model_name='proveedor', name='regimen_tributario',
            field=models.CharField(max_length=20, default='RESPONSABLE_IVA',
                choices=[('RESPONSABLE_IVA','Responsable de IVA'),
                         ('NO_RESPONSABLE','No Responsable de IVA'),
                         ('REGIMEN_SIMPLE','Régimen Simple'),
                         ('GRAN_CONTRIBUYENTE','Gran Contribuyente'),
                         ('ESPECIAL','Entidad sin ánimo de lucro')]),
        ),
        migrations.AddField(model_name='proveedor', name='responsable_iva',   field=models.BooleanField(default=True)),
        migrations.AddField(model_name='proveedor', name='gran_contribuyente', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='proveedor', name='agente_retenedor',  field=models.BooleanField(default=False)),
        migrations.AddField(model_name='proveedor', name='autoretenedor',     field=models.BooleanField(default=False)),
        migrations.AddField(model_name='proveedor', name='ciiu',              field=models.CharField(max_length=10, blank=True)),
        migrations.AddField(model_name='proveedor', name='cuenta_bancaria',   field=models.CharField(max_length=30, blank=True)),
        migrations.AddField(model_name='proveedor', name='banco',             field=models.CharField(max_length=100, blank=True)),
        migrations.AddField(model_name='proveedor', name='tipo_cuenta',       field=models.CharField(max_length=15, blank=True,
                                                                                   choices=[('Ahorros','Ahorros'),('Corriente','Corriente')])),
        migrations.AddField(model_name='proveedor', name='notas',             field=models.TextField(blank=True)),
        migrations.AddField(
            model_name='proveedor', name='creado_por',
            field=models.ForeignKey(blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proveedores_creados',
                to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelOptions(
            name='proveedor',
            options={'db_table': 'proveedores', 'ordering': ['razon_social'], 'verbose_name': 'Proveedor'},
        ),
    ]