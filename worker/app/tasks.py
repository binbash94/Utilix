from worker.app.worker import celery_app

@celery_app.task(name="worker.example.add")
def add(x: int, y: int) -> int:    # type: ignore[return-value]
    return x + y
