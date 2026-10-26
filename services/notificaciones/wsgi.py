"""Punto de entrada WSGI: `gunicorn wsgi:app` o `python wsgi.py` en local."""
import os

from notificaciones_service import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5002")), debug=True)
