# Generated by Django 4.2 on 2024-01-06 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0039_law_link_law_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='law',
            name='formatted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lawproject',
            name='formatted',
            field=models.BooleanField(default=False),
        ),
    ]
