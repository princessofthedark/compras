FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=autodis_compras.settings.production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

RUN adduser --disabled-password --no-create-home appuser
RUN mkdir -p /app/media && chown -R appuser:appuser /app/media
USER appuser

EXPOSE 8000

CMD ["gunicorn", "autodis_compras.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
