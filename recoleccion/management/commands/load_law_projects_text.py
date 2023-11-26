# Base command
from django.core.management.base import BaseCommand

# Django
from django.db.models import Q

# Components
from recoleccion.components.data_sources.law_projects_text_source import (
    DeputiesLawProjectsText,
    SenateLawProjectsText,
)
import logging
from recoleccion.models.law_project import LawProject
from recoleccion.utils.enums.project_chambers import ProjectChambers
from multiprocessing import Queue, Event, current_process
from queue import Empty
from time import sleep
import argparse
from recoleccion.components.process import StoppableProcess

DEFAULT_PROCESS_NUMBER = 5


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"
    num_processes = DEFAULT_PROCESS_NUMBER

    def add_arguments(self, parser):
        parser.add_argument("--processes", type=int, default=DEFAULT_PROCESS_NUMBER)
        parser.add_argument("--only-missing", action=argparse.BooleanOptionalAction)

    def worker_target(self, projects_queue, data_queue):
        this_process = current_process().name

        def get_text_from_source(number, source, year, project_id, text_source):
            try:
                text, link = text_source.get_text(number, source, year)
                return text, link
            except Exception:
                self.logger.error(
                    f"{this_process} > Error while getting text with {text_source.__name__}"
                    + f"for project with {project_id} id"
                    + f" and number: {number}, source: {source}, year: {year}",
                    exc_info=True,
                )
                return None, None

        try:
            project = projects_queue.get(timeout=2)

            # First get project text from deputies source
            text, link = get_text_from_source(
                project.deputies_number,
                project.deputies_source,
                project.deputies_year,
                project.deputies_project_id,
                DeputiesLawProjectsText,
            )

            # If text is empty, get it from senate source
            if not text:
                text, link = get_text_from_source(
                    project.senate_number,
                    project.senate_source,
                    project.senate_year,
                    project.senate_project_id,
                    SenateLawProjectsText,
                )

            # If text is still empty, get it from deputies source with the senate id
            if not text:
                text, link = get_text_from_source(
                    project.senate_number,
                    project.senate_source,
                    project.senate_year,
                    project.senate_project_id,
                    DeputiesLawProjectsText,
                )

            if text:
                data_queue.put((project, text, link))
                return False

            self.logger.info(
                f"{this_process} > No text found for project with deputies id: {project.deputies_project_id} and senate id: {project.senate_project_id}"
            )

        except Empty:
            self.logger.info(f"{this_process} > Projects queue empty")
            return True

        return False

    def writer_target(self, data_queue, workers_finished):
        this_process = current_process().name
        try:
            if workers_finished.is_set():
                self.logger.info(f"{this_process} > Bulk updating projects...")
                projects = []
                while not data_queue.empty():
                    data = data_queue.get(timeout=1)
                    project, text, link = data
                    text = text.replace("\x00", "\uFFFD")
                    link = link.replace("\x00", "\uFFFD")
                    project.text = text
                    project.link = link
                    projects.append(project)
                self.logger.info(f"{this_process} > Bulk updating {projects}...")
                LawProject.objects.bulk_update(
                    projects, ["text", "link"], batch_size=500
                )
                return True
            data = data_queue.get(timeout=1)
            project, text, link = data
            self.logger.info(
                f"{this_process} > Updating Project [id:{project.id}, deputy_id:{project.deputies_project_id}, senate_id:{project.senate_project_id}] "
            )
            text = text.replace("\x00", "\uFFFD")
            link = link.replace("\x00", "\uFFFD")
            LawProject.update(id=project.id, text=text, link=link)
            self.logger.info(
                f"{this_process} > Correctly updated Project [id:{project.id}, deputy_id:{project.deputies_project_id}, senate_id:{project.senate_project_id}]"
            )
        except Empty:
            pass  # To avoid locking into empty queue
        return True if workers_finished.is_set() else False

    def handle(self, *args, **options):
        self.num_processes = options.get("processes", self.num_processes)
        only_missing = options.get("only_missing", False)
        projects = (
            LawProject.objects.filter(Q(text=None) | Q(text="")).all()
            if only_missing
            else LawProject.objects.all()
        )
        self.logger.info(
            f"STARTING COMMAND: load_law_projects_text with {self.num_processes} processes"
        )
        self.projects_queue = Queue()
        self.data_queue = Queue()
        self.workers_finished = Event()
        for project in projects:
            self.projects_queue.put(project)
        self.workers = []
        self.writer = StoppableProcess(
            target=self.writer_target,
            args=(self.data_queue, self.workers_finished),
            name="Writer",
        )
        try:
            for i in range(self.num_processes):
                p = StoppableProcess(
                    target=self.worker_target,
                    args=(self.projects_queue, self.data_queue),
                    name=f"Worker-{i}",
                )
                self.workers.append(p)
            alive_workers = True
            while alive_workers:
                self.logger.info(
                    f"CURRENT STATE: \n\t- Projects queue size: {self.projects_queue.qsize()}\n\t- Data queue size: {self.data_queue.qsize()}"
                )
                alive_workers = [t.name for t in self.workers if not t.stopped()]
                self.logger.info(f"Alive workers: {str(alive_workers)}")
                sleep(1)
            self.logger.warning("No workers alive, explicitly stopping them...")
            for p in self.workers:
                p.stop_and_join()
            self.logger.info("All workers stopped. Finish writting data...")
            self.workers_finished.set()
            while not self.writer.stopped():
                self.logger.info(
                    f"Working...\n\t- Projects queue size: {self.projects_queue.qsize()}\n\t- Data queue size: {self.data_queue.qsize()}"
                )
                sleep(1)
            self.writer.stop_and_join()
            self.logger.info("Writer stopped")
            self.logger.info("Killing missing processes and queues...")
            self._stop_threads()
            self.logger.info("All processes stopped")
        except KeyboardInterrupt:
            self.logger.warning("Keyboard interrupt received. Stopping threads...")
            self._stop_threads()
        except BaseException as e:
            self.logger.error(f"Exception occurred: {repr(e)}. Stopping threads...")
            self._stop_threads()

        self.logger.info("FINISHED COMMAND: load_law_projects_text")

    def _stop_threads(self):
        self.logger.info(
            f"Projects remaining in workers queue: {self.projects_queue.qsize()}"
        )
        self.logger.info(
            f"Projects remaining in writer queue: {self.data_queue.qsize()}"
        )
        # To avoid the need of flushing the queues
        self.projects_queue.cancel_join_thread()
        self.data_queue.cancel_join_thread()
        for p in self.workers:
            p.stop_and_join()
        self.logger.info("Workers joined")
        self.writer.stop_and_join()
        self.logger.info("Writer joined")
        self.logger.info("All processes stopped")
