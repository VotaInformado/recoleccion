# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_text_source import (
    DeputiesLawProyectsText,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.models.law_project import LawProject
from recoleccion.utils.enums.project_chambers import ProjectChambers
from multiprocessing import Process, Queue, Event
from queue import Empty
from time import sleep


class Command(BaseCommand):
    logger = CustomLogger()
    help = "Load laws from the deputy source"

    # def add_arguments(self, parser):
    #     parser.add_argument("--starting-page", type=int, default=1)
    #     parser.add_argument("--ending-page", type=int, default=None)

    def worker(self, projects_queue, data_queue, stop_event):
        try:
            while not projects_queue.empty() or not stop_event.is_set():
                project = projects_queue.get(timeout=10)
                if project.origin_chamber == "Diputados":  # ProjectChambers.DEPUTIES:
                    num, source, year = project.deputies_project_id.split("-")
                    text, link = DeputiesLawProyectsText.get_text(num, source, year)
                    data_queue.put((project, text, link))
        except Empty:
            self.logger.info(f"Worker thread stopped")

    def writer(self, data_queue, stop_event):
        while not stop_event.is_set():
            data = data_queue.get()
            project, text, link = data
            LawProject.update(id=project.id, text=text, link=link)
            self.logger.info(
                f"Project {project.deputies_project_id} | {project.senate_project_id} updated"
            )

    def handle(self, *args, **options):
        projects = LawProject.objects.all()
        projects_queue = Queue()
        data_queue = Queue()
        for project in projects:
            projects_queue.put(project)
        threads = []
        stop_writer = Event()
        stop_workers = Event()
        writer_thread = Process(target=self.writer, args=(data_queue, stop_writer))
        writer_thread.start()
        try:
            for i in range(5):
                t = Process(
                    target=self.worker, args=(projects_queue, data_queue, stop_workers)
                )
                threads.append(t)
                t.start()
            while True:
                if projects_queue.empty() and data_queue.empty():
                    break
                self.logger.info(f"Projects queue size: {projects_queue.qsize()}")
                self.logger.info(f"Data queue size: {data_queue.qsize()}")
                sleep(1)
            stop_writer.set()
            for t in threads:
                t.join()
            writer_thread.join()
        except:
            import pdb; pdb.set_trace()
            self.logger.info("Exception occurred. Stopping threads...")
            stop_workers.set()
            stop_writer.set()
            for t in threads:
                t.join()
            writer_thread.join()
