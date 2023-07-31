# Generated by Django 4.2 on 2023-07-27 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0011_law_associated_project_law_project_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lawproject',
            name='status',
            field=models.CharField(choices=[('WITHDRAWN', 'Retirado'), ('HALF_SANCTION', 'Media sanción'), ('APPROVED', 'Aprobado'), ('REJECTED', 'Rechazado')], max_length=15, null=True),
        ),
    ]
