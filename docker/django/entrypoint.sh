#!/bin/sh
# Arranque del monolito dentro del contenedor.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0

# Datos de demostracion solo la primera vez (seed_demo falla si ya existen).
if [ "${SEED_DEMO:-0}" = "1" ]; then
  python manage.py seed_demo || echo "seed_demo omitido: los datos ya existen"
fi

exec "$@"
