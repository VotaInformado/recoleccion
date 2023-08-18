# Base command
from django.core.management.base import BaseCommand

# Django
from django.db.models import Q

# Components
from recoleccion.components.data_sources.law_projects_text_source import (
    DeputiesLawProyectsText,
    SenateLawProyectsText,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.models.law_project import LawProject
from recoleccion.utils.enums.project_chambers import ProjectChambers
from multiprocessing import Process, Queue, Event, current_process, active_children
from queue import Empty
from time import sleep
import argparse

DEFAULT_PROCESS_NUMBER = 5


def process(func):
    def wrapper_func(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            pass  # To avoid printing the stack trace when force stopping the process

    return wrapper_func


class Command(BaseCommand):
    logger = CustomLogger()
    help = "Load laws from the deputy source"
    num_processes = DEFAULT_PROCESS_NUMBER

    def add_arguments(self, parser):
        parser.add_argument("--processes", type=int, default=DEFAULT_PROCESS_NUMBER)
        parser.add_argument("--only-missing", action=argparse.BooleanOptionalAction)

    @process
    def worker(self, projects_queue, data_queue, stop_event):
        this_process = current_process().name
        while not stop_event.is_set():
            try:
                project = projects_queue.get(timeout=2)
                if project.origin_chamber == ProjectChambers.DEPUTIES:
                    num, source, year = project.deputies_project_id.split("-")
                    text, link = DeputiesLawProyectsText.get_text(num, source, year)
                    data_queue.put((project, text, link))
                elif project.origin_chamber == ProjectChambers.SENATORS:
                    parts = project.senate_project_id.split("-")
                    # Ugly FIX: some projects have a wrong format TODO: fix
                    if len(parts) == 3:
                        num, source, year = parts
                    elif len(parts) == 2:
                        num, year = parts
                        source = "S"
                    else:
                        continue
                    text, link = SenateLawProyectsText.get_text(num, source, year)
                    # TODO: if text is empty try to get text with deputies Projects source
                    data_queue.put((project, text, link))
            except Empty:
                self.logger.info(f"{this_process} > Projects queue empty")
                break

    @process
    def writer(self, data_queue, stop_event):
        while not stop_event.is_set():
            try:
                data = data_queue.get(timeout=1)
                project, text, link = data
                self.logger.info(
                    f"Writer > Updating Project [id:{project.id}, deputy_id:{project.deputies_project_id}, senate_id:{project.senate_project_id}] "
                )
                text = text.replace("\x00", "\uFFFD")
                link = link.replace("\x00", "\uFFFD")
                LawProject.update(id=project.id, text=text, link=link)
                self.logger.info(
                    f"Writer > Correctly updated Project [id:{project.id}, deputy_id:{project.deputies_project_id}, senate_id:{project.senate_project_id}]"
                )
            except Empty:
                pass
            except Exception as e:
                self.logger.error(f"Writer > Error: {repr(e)}")
        self.logger.info(f"Writer > Stopped")

    def handle(self, *args, **options):
        self.num_processes = options.get("processes", self.num_processes)
        only_missing = options.get("only_missing", False)
        projects = (
            LawProject.objects.filter(Q(text=None) | Q(text="")).all()
            if only_missing
            else LawProject.objects.all()
        )
        projects = projects[:10]
        self.projects_queue = Queue()
        self.data_queue = Queue()
        for project in projects:
            self.projects_queue.put(project)
        self.workers = []
        self.stop_writer = Event()
        self.stop_workers = Event()
        self.writer_thread = Process(
            target=self.writer, args=(self.data_queue, self.stop_writer), name="Writer"
        )
        self.writer_thread.start()
        try:
            for i in range(self.num_processes):
                t = Process(
                    target=self.worker,
                    args=(self.projects_queue, self.data_queue, self.stop_workers),
                    name=f"Worker-{i}",
                )
                self.workers.append(t)
                t.start()
            alive_workers = True
            while alive_workers:
                self.logger.info(
                    f"CURRENT STATE: \n\t- Projects queue size: {self.projects_queue.qsize()}\n\t- Data queue size: {self.data_queue.qsize()}"
                )
                alive_workers = [t.name for t in self.workers if t.is_alive()]
                self.logger.info(f"Alive workers: {str(alive_workers)}")
                sleep(1)
            self.logger.warning("No workers alive, explicitly stopping them...")
            self.stop_workers.set()
            for t in self.workers:
                t.join()
            self.logger.info("All workers stopped")
            while not self.data_queue.empty():
                self.logger.info(
                    f"Working...\n\t- Projects queue size: {self.projects_queue.qsize()}\n\t- Data queue size: {self.data_queue.qsize()}"
                )
                sleep(1)
            self.stop_writer.set()
            self.writer_thread.join()
            self.logger.info("All processes stopped")
        except:
            self.logger.error("Exception occurred. Stopping threads...")
            self.logger.info(
                f"Projects remaining in workers queue: {self.projects_queue.qsize()}"
            )
            self.logger.info(
                f"Data remaining in writer queue: {self.data_queue.qsize()}"
            )
            self._stop_threads()

    def _stop_threads(self):
        # To dont need to flush queues
        self.projects_queue.cancel_join_thread()
        self.data_queue.cancel_join_thread()
        self.stop_workers.set()
        for t in self.workers:
            t.join()
        self.logger.info("Workers joined")
        self.stop_writer.set()
        self.writer_thread.join()
        self.logger.info("Writer joined")
        self.logger.info("All processes stopped")
