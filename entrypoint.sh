#!/usr/bin/env sh
set -e

# Apply database migrations
echo "Applying database migrations"
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files"
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn"
exec gunicorn djangoMVP.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-3} --log-level info 