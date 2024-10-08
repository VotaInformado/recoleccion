import time
from django.conf import settings
from datetime import datetime, timedelta

# Logging
import logging

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from django.core.management import call_command

logger = logging.getLogger(__name__)


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


@util.close_old_connections
def call_command_task(command_name):
    call_command(command_name)


update_deposits_status_start_time = datetime.now() + timedelta(minutes=1)

# Define jobs run times here: for example
# job_triggers = {"load_laws_text": CronTrigger(minute="*/4")}

job_triggers = {}

class Command(BaseCommand):
    help = "Runs APScheduler."

    logging.basicConfig()
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        for task, trigger in job_triggers.items():
            scheduler.add_job(
                call_command_task,
                args=(task,),
                id=task,
                replace_existing=True,
                max_instances=1,
                trigger=trigger,
            )
            logger.info(f"Added job '{task}'.")

        # Delete old job executions from the database
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job: 'delete_old_job_executions'.")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
