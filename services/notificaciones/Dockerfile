# Microservicio de Notificaciones (Flask) - imagen independiente del monolito.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home notif && chown -R notif /app
USER notif

EXPOSE 5002

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5002/api/v2/notificaciones/salud')"

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5002", "--workers", "2", "--threads", "4", "--preload", "--access-logfile", "-"]
