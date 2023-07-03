# Generated by Django 4.2 on 2023-07-03 03:48

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('informacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='person',
            table='person',
        ),
        migrations.CreateModel(
            name='DeputySeat',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deputy_id', models.CharField(max_length=10)),
                ('district', models.CharField(max_length=150)),
                ('party', models.CharField(max_length=150)),
                ('start_of_term', models.DateField()),
                ('end_of_term', models.DateField()),
                ('person_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deputy_seat', to='informacion.person')),
            ],
            options={
                'db_table': 'deputy_seat',
                'unique_together': {('person_id', 'start_of_term', 'end_of_term')},
            },
        ),
    ]
