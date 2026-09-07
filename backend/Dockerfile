FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser \
    && mkdir -p /app/storage/uploads /app/storage/cleaned \
    && chown -R appuser:appuser /app

COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["celery", "-A", "app.core.celery_app:celery_app", "worker", "--loglevel=INFO"]
