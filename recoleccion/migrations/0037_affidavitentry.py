# Generated by Django 4.2 on 2023-12-21 01:45

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0036_alter_partylinkingdecision_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AffidavitEntry',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('linking_id', models.UUIDField(editable=False, null=True)),
                ('person_full_name', models.CharField(max_length=255)),
                ('year', models.IntegerField()),
                ('affidavit_type', models.CharField(choices=[('Inicial', 'Inicial'), ('Anual', 'Anual'), ('Final', 'Final')], max_length=10)),
                ('value', models.DecimalField(decimal_places=2, max_digits=20)),
                ('source', models.CharField(max_length=255)),
                ('person', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='affidavits', to='recoleccion.person')),
            ],
            options={
                'unique_together': {('person_full_name', 'year')},
            },
        ),
    ]
