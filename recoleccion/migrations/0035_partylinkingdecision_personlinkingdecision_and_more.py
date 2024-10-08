# Generated by Django 4.2 on 2023-12-01 23:59

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recoleccion', '0034_missingrecord'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartyLinkingDecision',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('linking_id', models.UUIDField(editable=False, null=True)),
                ('decision', models.CharField(choices=[('APPROVED', 'Aprobado'), ('DENIED', 'Denegado'), ('PENDING', 'Pendiente')], default='PENDING', max_length=10, null=True)),
                ('messy_denomination', models.CharField(help_text='Messy denomination', max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PersonLinkingDecision',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date time on which the object was created.', verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='Date time on which the object was last modified.', verbose_name='updated at')),
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('linking_id', models.UUIDField(editable=False, null=True)),
                ('decision', models.CharField(choices=[('APPROVED', 'Aprobado'), ('DENIED', 'Denegado'), ('PENDING', 'Pendiente')], default='PENDING', max_length=10, null=True)),
                ('messy_name', models.CharField(help_text='Messy full name', max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='personlinking',
            name='person',
        ),
        migrations.AddField(
            model_name='authorship',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='deputyseat',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='law',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='lawproject',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='missingrecord',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='party',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='partydenomination',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='senateseat',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='socialdata',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='linking_id',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.DeleteModel(
            name='PartyLinking',
        ),
        migrations.DeleteModel(
            name='PersonLinking',
        ),
        migrations.AddField(
            model_name='personlinkingdecision',
            name='person',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='linking', to='recoleccion.person'),
        ),
        migrations.AddField(
            model_name='partylinkingdecision',
            name='party',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='linking', to='recoleccion.party'),
        ),
    ]
