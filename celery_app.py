from celery import Celery
from celery.schedules import crontab
from decouple import config

broker = config("CELERY_HOST")

app = Celery("main", broker=broker)

app.conf.update(
    result_backend=broker,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Berlin",
    enable_utc=True,
)

app.conf.beat_schedule = {
    "check_all": {"task": "main.check_all", "schedule": crontab(hour=10, minute=5)}
}
