# Microservicio de Pagos (Flask) - imagen independiente del monolito.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Usuario sin privilegios: el servicio no necesita root.
RUN useradd --create-home pagos && chown -R pagos /app
USER pagos

EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/v2/pagos/salud')"

# Hilos: mientras un worker espera la confirmacion de Django, otro atiende la
# verificacion de referencia que Django hace de vuelta.
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--preload", "--access-logfile", "-"]
