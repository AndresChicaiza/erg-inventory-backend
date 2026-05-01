from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Agrega:
      - Modelo Sede
      - Campo sede (FK) al modelo Usuario
      - Campo telefono al modelo Usuario
      - Actualiza ROL_CHOICES con los 7 roles definitivos
    """

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # 1. Crear tabla sedes
        migrations.CreateModel(
            name='Sede',
            fields=[
                ('id',        models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nombre',    models.CharField(max_length=100, unique=True)),
                ('tipo',      models.CharField(
                                  max_length=10,
                                  choices=[
                                      ('FABRICA','Fábrica'),('TIENDA','Tienda'),
                                      ('MERCADEO','Mercadeo'),('LOGISTICA','Logística'),
                                      ('OFICINA','Oficina'),
                                  ]
                              )),
                ('ciudad',    models.CharField(max_length=100, default='Cali')),
                ('direccion', models.TextField(blank=True)),
                ('telefono',  models.CharField(max_length=25, blank=True)),
                ('estado',    models.CharField(max_length=10, choices=[('Activa','Activa'),('Inactiva','Inactiva')], default='Activa')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'sedes', 'ordering': ['nombre'], 'verbose_name': 'Sede'},
        ),

        # 2. Agregar FK sede a Usuario
        migrations.AddField(
            model_name='usuario',
            name='sede',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios',
                to='users.sede',
            ),
        ),

        # 3. Agregar teléfono a Usuario
        migrations.AddField(
            model_name='usuario',
            name='telefono',
            field=models.CharField(blank=True, max_length=25),
        ),

        # 4. Actualizar ROL_CHOICES (solo cambia los choices, no la columna)
        migrations.AlterField(
            model_name='usuario',
            name='rol',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('Administrador', 'Administrador'),
                    ('Contador',      'Contador'),
                    ('Vendedor',      'Vendedor'),
                    ('Logistica',     'Logística'),
                    ('JefeFabrica',   'Jefe de Fábrica'),
                    ('Bodeguero',     'Bodeguero'),
                    ('RRHH',          'RRHH'),
                ],
                default='Vendedor',
            ),
        ),
    ]