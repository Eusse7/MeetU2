# Microservicio de Social (Flask) - imagen independiente del monolito.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home social && chown -R social /app
USER social

EXPOSE 5001

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5001/api/v2/social/salud')"

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "--preload", "--access-logfile", "-"]
