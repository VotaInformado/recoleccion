# Generated by Django 4.2 on 2024-01-21 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0044_socialdata_person_last_name_socialdata_person_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialdata',
            name='person',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='social_data', to='recoleccion.person'),
        ),
    ]
