# Generated by Django 4.2 on 2023-09-07 01:34

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0028_rename_party_vote_party_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartyLinking',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('denomination', models.CharField(max_length=200)),
                ('compared_against', models.CharField(max_length=200, null=True)),
                ('decision', models.CharField(choices=[('APPROVED', 'Aprobado'), ('DENIED', 'Denegado')], max_length=10, null=True)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linking', to='recoleccion.party')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
