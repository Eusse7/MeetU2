# Microservicio de Catalogo (Flask) - imagen independiente del monolito.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home catalogo && chown -R catalogo /app
USER catalogo

EXPOSE 5003

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5003/api/v2/catalogo/salud')"

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5003", "--workers", "2", "--threads", "4", "--preload", "--access-logfile", "-"]
