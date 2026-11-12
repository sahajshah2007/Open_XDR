import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "openxdr_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_timeout=1,
    broker_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1},
    task_publish_retry=False,
    beat_schedule={"dispatch-pending-events": {"task": "detection.dispatch_pending", "schedule": 10.0},
                   "finalize-experiments": {"task":"experiments.finalize_pending","schedule":3.0}},
    include=['app.services.detection','app.services.experiments']
)

# Ensure all models are loaded for SQLAlchemy's metadata before tasks execute
from app.models import user, host, event, alert, incident, pipeline, experiment
