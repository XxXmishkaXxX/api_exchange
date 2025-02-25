from celery import Celery
from core.config import settings
from datetime import timedelta

app  = Celery(
    "auth_service",
    broker=settings.CELERY_REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)

app.conf.beat_schedule = {
    'delete_inactive_users_daily': {
        'task': 'tasks.delete_inactive_users',
        'schedule': timedelta(days=1),
    },
}