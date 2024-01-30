from django.core.management.base import BaseCommand
import logging
from tqdm import tqdm

# Project
from recoleccion.models import Person


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Eliminates repeated seats for each legislator"

    def delete_repeated_seats(self, legislator_seats):
        deleted_seats = []
        total_deleted_seats = 0
        for seat in legislator_seats:
            if seat.pk in deleted_seats:
                continue
            seat_from_year, seat_to_year = seat.start_of_term.year, seat.end_of_term.year
            other_seats = legislator_seats.filter(
                start_of_term__year=seat_from_year, end_of_term__year=seat_to_year
            ).exclude(id=seat.id)
            if other_seats.exists():
                logger.info(f"Found duplicate seats for {seat.person.full_name} in {seat_from_year}-{seat_to_year}")
                logger.info(f"Removing {other_seats.count()} seats...")
                total_deleted_seats += other_seats.count()
                deleted_seats.extend([os.pk for os in other_seats.all()])
                other_seats.delete()
        return total_deleted_seats

    def handle(self, *args, **options):
        self.deleted_deputy_seats = self.deleted_senate_seats = 0
        for person in tqdm(Person.objects.all()):
            deputy_seats = person.deputy_seats.all()
            senate_seats = person.senate_seats.all()
            deleted_deputy_seats = self.delete_repeated_seats(deputy_seats)
            deleted_senate_seats = self.delete_repeated_seats(senate_seats)
            self.deleted_deputy_seats += deleted_deputy_seats
            self.deleted_senate_seats += deleted_senate_seats

        logger.info(f"Deleted {self.deleted_deputy_seats} deputy seats")
        logger.info(f"Deleted {self.deleted_senate_seats} senate seats")
