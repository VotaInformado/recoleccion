# Generated by Django 4.2 on 2023-10-04 00:55
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("recoleccion", "0031_alter_partydenomination_denomination"),
    ]

    operations = [
        migrations.RenameField(
            model_name="authorship",
            old_name="party",
            new_name="party_name",
        ),
        migrations.AddField(
            model_name="authorship",
            name="party",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="authorships",
                to="recoleccion.party",
            ),
        ),
    ]
