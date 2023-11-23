from multiprocessing import Process, Event, current_process
import logging


class StoppableProcess(Process):
    """
    Custom Process class that will run the target function
    in a loop until the stop method is called.

    Calling the stop method will set the stop event and
    join the process.

    In order finish the process without calling the stop
    method, the target function must return True when the
    process has finished its work.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, target, args=(), kwargs={}, auto_start=True, **other):
        target = self._wrap_target(target)
        super().__init__(target=target, args=args, kwargs=kwargs, **other)
        self._stop_event = Event()
        if auto_start:
            self.start()

    def stop(self):
        self._stop_event.set()

    def stop_and_join(self):
        self.stop()
        self.join()

    def stopped(self):
        return self._stop_event.is_set()

    def _wrap_target(self, target):
        def wrapper(*args, **kwargs):
            this_process = current_process().name
            try:
                while not self.stopped():
                    if target(*args, **kwargs):
                        self.stop()
            except KeyboardInterrupt:
                # To avoid printing the stack trace when force
                # stopping the process in the main process
                pass
            except BaseException as e:
                import traceback

                self.logger.error(
                    f"{this_process} > BaseException ocurred", exc_info=True
                )
            self.stop()
            self.logger.warning(f"{this_process} > Stopped")

        return wrapper
