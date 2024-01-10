# Django
from django.contrib import admin

# Project
from recoleccion.models import Party, PartyDenomination, SenateSeat, DeputySeat, Vote, Authorship, PartyLinkingDecision
from recoleccion.utils.enums.party_relation_types import PartyRelationTypes
from django.db import IntegrityError


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ["id", "main_denomination"]
    list_filter = ["id", "main_denomination"]
    search_fields = ["id", "main_denomination"]

    actions = ["change_party_name", "create_sub_party"]

    def change_party_name(self, request, queryset):
        new_denomination = input("Ingrese el nuevo nombre del partido: ")
        if not new_denomination:
            self.message_user(request, "Debe ingresar un nombre", level="ERROR")
            return
        party: Party = queryset.first()
        if new_denomination == party.main_denomination:
            self.message_user(request, "El nombre no puede ser el mismo", level="ERROR")
            return
        try:
            PartyDenomination.objects.create(party=party, denomination=new_denomination)
        except Exception:
            # Ya existía la denominación alternativa, no es un problema
            pass
        party.main_denomination = new_denomination
        try:
            party.save()
        except Exception as e:
            self.message_user(request, f"Error: {e}", level="ERROR")
            return

    change_party_name.short_description = "Cambiar nombre"

    def create_sub_party(self, request, queryset):
        party_id = input("Ingrese el id del super-partido: ")
        sub_party_id = input("Ingrese el id del sub-partido: ")
        party = Party.objects.get(id=party_id)
        self.message_user(request, f"Party: {party.main_denomination}", level="INFO")
        sub_party = Party.objects.filter(id=sub_party_id).first()
        relation_choices = [relation_type[0] for relation_type in PartyRelationTypes.choices]
        relation_type = input(
            f"Ingrese el tipo de relación entre {party.main_denomination} y {sub_party.main_denomination} "
            f"({relation_choices}): "
        )
        if relation_type not in relation_choices:
            self.message_user(request, "Opción inválida", level="ERROR")
            return
        self.message_user(request, f"Creando sub partido {sub_party.main_denomination}...", level="INFO")
        if not sub_party:
            self.message_user(
                request, f"Sub partido {sub_party.main_denomination} has already been deleted...", level="ERROR"
            )
        else:
            self.message_user(request, f"Sub partido: {sub_party.main_denomination}", level="INFO")
        sub_party_senate_seats = SenateSeat.objects.filter(party=sub_party)
        sub_party_deputy_seats = DeputySeat.objects.filter(party=sub_party)
        sub_party_votes = Vote.objects.filter(party=sub_party)
        sub_party_autorships = Authorship.objects.filter(party=sub_party)
        sub_party_linking_decisions = PartyLinkingDecision.objects.filter(party=sub_party)
        self.message_user(request, f"Updated {len(sub_party_senate_seats)} senate seats", level="INFO")
        sub_party_senate_seats.update(party=party)
        self.message_user(request, f"Updated {len(sub_party_deputy_seats)} deputy seats", level="INFO")
        sub_party_deputy_seats.update(party=party)
        self.message_user(request, f"Updated {len(sub_party_votes)} votes", level="INFO")
        sub_party_votes.update(party=party)
        self.message_user(request, f"Updated {len(sub_party_autorships)} authorships", level="INFO")
        sub_party_autorships.update(party=party)
        self.message_user(request, f"Updated {len(sub_party_linking_decisions)} linking decisions", level="INFO")
        sub_party_linking_decisions.update(party=party)
        if not sub_party:
            return
        sub_party.delete()
        try:
            PartyDenomination.objects.create(
                party=party, denomination=sub_party.main_denomination, relation_type=relation_type
            )
        except IntegrityError:
            self.message_user(request, f"Sub party {sub_party.main_denomination} already exists", level="ERROR")
        self.message_user(request, f"Deleted sub party {sub_party.main_denomination}", level="INFO")

    create_sub_party.short_description = "Crear sub partido"
