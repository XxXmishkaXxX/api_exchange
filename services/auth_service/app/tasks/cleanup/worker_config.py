from celery import Celery
from core.config import settings
from datetime import timedelta

cleanup_app  = Celery(
    "cleanup_worker",
    broker=settings.CLEANUP_REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.clear"]
)

cleanup_app .conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)

cleanup_app.conf.beat_schedule = {
    'delete_inactive_accounts_daily': {
        'task': 'tasks.delete_inactive_accounts',
        'schedule': timedelta(days=1),
    },
}