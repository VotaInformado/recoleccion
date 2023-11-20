from django.core.management.base import BaseCommand
import threading


class CustomCommand(BaseCommand):
    THREAD_AMOUNT = 8
    index_name = None

    class Meta:
        abstract = True

    def handle(self, *args, **options):
        threads = []
        for index in range(self.THREAD_AMOUNT):
            options["step_size"] = self.THREAD_AMOUNT
            index_name = self.index_name  # starting_page, starting_period or starting_year
            options[index_name] = index
            thread = threading.Thread(name=f"Thread {index+1}", target=self.main_function, kwargs=options)
            threads.append(thread)
            thread.start()
            if self.reverse_index:
                index -= 1
            else:
                index += 1

        for thread in threads:
            thread.join()

    def main_function(self):
        raise NotImplementedError


class YearThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = True
        self.index_name = "starting_year"


class PageThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_page"


class PeriodThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_period"
