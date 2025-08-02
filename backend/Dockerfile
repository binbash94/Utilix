############################################
#  backend/Dockerfile
############################################

# ---------- build stage ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# install deps from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels /wheels/*.whl

# ⬇︎ copy *this directory* (the build context) into /app/backend
#    so your imports remain `backend.app.main`, etc.
COPY . /app/backend

# gunicorn entry
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "backend.app.main:app", "--bind", "0.0.0.0:8000"]
