# Generated by Django 5.2 on 2025-05-25 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0012_intento'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='fecha_limite',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
