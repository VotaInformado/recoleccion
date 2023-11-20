import logging
from axiom import Client
from datetime import datetime
from django.conf import settings

class AxiomHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.axiom = Client()

    def format(self, record):
        return {
            "_time": datetime.now().isoformat(),
            "level": record.levelname,
            "thread": record.threadName,
            "message": record.getMessage(),
            "traceback": record.exc_text if record.exc_text else None,
            "stacktrace": record.stack_info if record.stack_info else None,
        }

    def emit(self, record):
        try:
            event = self.format(record)
            self.axiom.ingest_events(dataset=settings.AXIOM_DATASET, events=[event])
        except Exception as e:
            self.handleError(record)
