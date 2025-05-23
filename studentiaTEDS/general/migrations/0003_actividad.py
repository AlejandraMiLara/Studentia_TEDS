# Generated by Django 5.2 on 2025-05-07 19:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0002_curso_configuracioncurso_alumnocurso'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='actividades/')),
                ('entregable', models.BooleanField(default=True)),
                ('generado_por_ia', models.BooleanField(default=False)),
                ('titulo', models.CharField(max_length=255)),
                ('contenido', models.TextField()),
                ('permite_entrega_tardia', models.BooleanField(default=False)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='general.curso')),
                ('docente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actividades_creadas', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
