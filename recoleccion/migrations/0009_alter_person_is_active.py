# Generated by Django 4.2 on 2023-07-23 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0008_remove_deputyseat_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
