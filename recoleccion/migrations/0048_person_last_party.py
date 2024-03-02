# Generated by Django 4.2 on 2024-03-02 12:53

from django.db import migrations, models
import django.db.models.deletion
from recoleccion.models import Person


class Migration(migrations.Migration):

    def set_last_party(apps, schema_editor):
        for person in Person.objects.all():
            person.last_party = person.get_last_party()
            person.save()

    dependencies = [
        ("recoleccion", "0047_deputyseat_source_law_source_missingrecord_source_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="last_party",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="recoleccion.party"),
        ),
        migrations.RunPython(set_last_party),
    ]
