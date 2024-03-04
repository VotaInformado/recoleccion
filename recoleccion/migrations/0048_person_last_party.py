# Generated by Django 4.2 on 2024-03-02 12:53

from django.db import migrations, models
import django.db.models.deletion
from recoleccion.models import Person as PersonModel
from recoleccion.models.party import Party


class Migration(migrations.Migration):

    def set_last_party(apps, schema_editor):
        Person: PersonModel = apps.get_model("recoleccion", "Person")
        for person in Person.objects.all():
            party: Party = person.get_last_party()
            person.last_party = party.main_denomination if party else None
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
