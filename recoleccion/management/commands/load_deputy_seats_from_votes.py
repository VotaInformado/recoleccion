# One time command# One time command
from django.core.management.base import BaseCommand
from django.db import IntegrityError
import logging
from tqdm import tqdm
import datetime as dt

# Project
from recoleccion.models import DeputySeat, Person, Vote

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def person_has_seat_at_vote_date(self, legislator: Person, vote_date: dt.date):
        # We only want deputies information
        for seat in legislator.deputy_seats.all():
            if seat.start_of_term <= vote_date <= seat.end_of_term:
                return True
        return False

    def is_even(self, number: int):
        return number % 2 == 0

    def is_after_elections_date(self, vote_date: dt.date):
        # caso no tan borde, por ejemplo un voto del 20-12-XXXX significa que el período es
        # entre 10-12-XXXX y 9-12-XXXX+4
        return vote_date.month == 12 and vote_date.day > 9

    def calculate_legislator_range(self, vote_date: int):
        # Como vamos de atrás para adelante, lo más probable es que el primer voto que encontremos
        # Sea cercano al final del rango, así que:
        # Fin de rango = voto_year si voto_year es impar, voto_year + 1 si voto_year es par
        # Por lo que vi, el rango va de 10/12/año a 9/12/año+4
        vote_year = vote_date.year
        if self.is_after_elections_date(vote_date):
            end_year = vote_year + 4
            start_year = vote_year
        end_year = vote_year + 1 if self.is_even(vote_year) else vote_year
        start_year = end_year - 4
        start_year_date = dt.date(year=start_year, month=12, day=10)
        end_year_date = dt.date(year=end_year, month=12, day=9)
        return (start_year_date, end_year_date)

    def create_seat(self, legislator: Person, seat_range: tuple, vote):
        start_date, end_date = seat_range
        party = vote.party or None
        party_name = vote.party_name
        try:
            DeputySeat.objects.create(
                person=legislator,
                start_of_term=start_date,
                end_of_term=end_date,
                party=party,
                party_name=party_name,
                source="Diputados (votos)",
            )
            self.created_seats += 1
        except IntegrityError as e:
            if vote.date.year > 2007:  # demasiadas coincidencias en 2007
                logger.info(
                    f"Seat already exists: legislator id: {legislator.id}, start_date: {start_date}, end_date: {end_date}"
                )
            return

    def handle(self, *args, **options):
        self.created_seats = 0
        votes = Vote.objects.filter(person_id__isnull=False, source="Diputados", date__year__lt=2008).order_by("-date")
        for i, vote in enumerate(tqdm(votes)):
            if i % 1000 == 0:
                logger.info(f"Seats created (out of {i} votes): {self.created_seats}")
            vote_legislator = vote.person
            if self.person_has_seat_at_vote_date(vote_legislator, vote.date):
                continue
            seat_range = self.calculate_legislator_range(vote.date)
            self.create_seat(vote_legislator, seat_range, vote)
        logger.info(f"Total seats created: {self.created_seats}")
