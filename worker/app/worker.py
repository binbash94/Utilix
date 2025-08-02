from celery import Celery
import os

# ---------------------------------------------------------------------
#  Celery application
# ---------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "land_saas_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,   # store task results in Redis as well
    include=[
        "worker.app.tasks",   # where you’ll add real async jobs
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# ---------------------------------------------------------------------
#  A tiny health‑check task
# ---------------------------------------------------------------------
@celery_app.task(name="worker.health.ping")
def ping() -> str:       # type: ignore[return-value]
    return "pong"
