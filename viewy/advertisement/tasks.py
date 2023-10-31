from celery import shared_task
import datetime

@shared_task
def print_current_time():
    print(f"Current Time: {datetime.datetime.now()}")