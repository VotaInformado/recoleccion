import os
import logging
import colorlog

# Django settings
from django.conf import settings


class CustomLogger:
    def __init__(self, name=__name__, log_file_path=None, log_level=None, threading=False):
        self.logger = logging.getLogger(name)
        log_level = log_level or getattr(settings, "log_level", None) or "INFO"
        self.logger.setLevel(log_level)

        # Prevent the log messages from being duplicated in the output.
        self.logger.propagate = False

        if any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            return

        if threading:
            format = "\n%(log_color)s%(levelname)-8s%(white)s(%(threadName)s) %(message)s"
        else:
            format = "\n%(log_color)s%(levelname)-8s%(white)s(%(threadName)s) %(message)s"

        log_formatter = colorlog.ColoredFormatter(
            format,
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
            secondary_log_colors={},
            style="%",
        )

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        # create formatter
        ch.setFormatter(log_formatter)

        # add ch to logger
        self.logger.addHandler(ch)

        if log_file_path:
            log_dir = os.path.dirname(log_file_path)
            os.makedirs(log_dir, exist_ok=True)

            fh = logging.FileHandler(log_file_path)
            fh.setLevel(log_level)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

            self.logger.addHandler(fh)

    def debug(self, message, exc_info=False):
        self.logger.debug(message, exc_info=exc_info)

    def info(self, message, exc_info=False):
        self.logger.info(message, exc_info=exc_info)

    def warning(self, message, exc_info=False):
        self.logger.warning(message, exc_info=exc_info)

    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message, exc_info=False):
        self.logger.critical(message, exc_info=exc_info)
