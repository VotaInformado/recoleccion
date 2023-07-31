# Generated by Django 4.2 on 2023-07-26 23:26

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0009_alter_person_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='LawProject',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('deputies_project_id', models.CharField(max_length=30, null=True, unique=True)),
                ('senate_project_id', models.CharField(max_length=30, null=True, unique=True)),
                ('origin_chamber', models.CharField(choices=[('SENATORS', 'Cámara de Senadores'), ('DEPUTIES', 'Cámara de Diputados')], max_length=10)),
                ('title', models.TextField()),
                ('publication_date', models.DateField(null=True)),
                ('deputies_file', models.CharField(max_length=30, null=True)),
                ('senate_file', models.CharField(max_length=30, null=True)),
                ('deputies_header_file', models.CharField(max_length=30, null=True)),
                ('senate_header_file', models.CharField(max_length=30, null=True)),
                ('status', models.CharField(choices=[('WITHDRAWN', 'Retirado'), ('HALF_SANCTION', 'Media sanción'), ('APPROVED', 'Aprobado'), ('REJECTED', 'Rechazado')], max_length=15)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
