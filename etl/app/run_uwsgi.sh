#!/usr/bin/env bash

set -euo pipefail

python manage.py migrate --fake-initial --noinput
python manage.py collectstatic --noinput

exec uwsgi --strict --ini /opt/app/uwsgi.ini


