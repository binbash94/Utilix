############################################
#  worker/Dockerfile   (build context = project root)
############################################
FROM python:3.12-slim
WORKDIR /app

# --- install Celery requirements ----------
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- copy source -------------------------------------------------------------
# everything Celery imports must be inside the image
COPY backend  /app/backend
COPY worker/app /app/worker/app

# --- start Celery worker ------------------
CMD ["celery", "-A", "worker.app.worker.celery_app", "worker", "--loglevel=info", "-Q", "default"]
