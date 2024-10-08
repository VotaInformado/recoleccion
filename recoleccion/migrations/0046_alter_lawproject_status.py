# Generated by Django 4.2 on 2024-01-23 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0045_alter_socialdata_person'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lawproject',
            name='status',
            field=models.CharField(choices=[('ORIGIN_CHAMBER_COMISSION', 'En comisiones, cámara de origen'), ('ORIGIN_CHAMBER_SENTENCE', 'Con dictamen de comisiones, cámara de origen'), ('HALF_SANCTION', 'Media sanción'), ('REVISION_CHAMBER_COMISSION', 'En comisiones, cámara revisora'), ('REVISION_CHAMBER_SENTENCE', 'Con dictamen de comisiones, cámara revisora'), ('WITHDRAWN', 'Retirado'), ('APPROVED', 'Aprobado'), ('REJECTED', 'Rechazado')], default='ORIGIN_CHAMBER_COMISSION', max_length=30),
        ),
    ]
