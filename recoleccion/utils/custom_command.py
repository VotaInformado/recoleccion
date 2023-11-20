from django.core.management.base import BaseCommand
import threading


class CustomCommand(BaseCommand):
    THREAD_AMOUNT = 8

    class Meta:
        abstract = True

    def handle(self, *args, **options):
        threads = []
        reverse_index = getattr(self, "reverse_index", False)
        for index in range(self.THREAD_AMOUNT):
            options["step_size"] = self.THREAD_AMOUNT
            options["index"] = index
            thread = threading.Thread(name=f"Thread {index+1}", target=self.main_function, kwargs=options)
            threads.append(thread)
            thread.start()
            if reverse_index:
                index -= 1
            else:
                index += 1

        for thread in threads:
            thread.join()

    def main_function(self):
        raise NotImplementedError
