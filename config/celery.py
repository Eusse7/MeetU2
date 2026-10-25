import os
from celery import Celery

# Configura el módulo de configuración de Django para 'celery'.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("meetu2")

# Lee la configuración de Celery desde settings.py usando el prefijo CELERY_.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodescubre tareas en todas las aplicaciones instaladas de Django (tasks.py).
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
