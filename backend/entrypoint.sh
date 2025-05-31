#!/bin/sh


echo "Waiting for PostgreSQL"

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL started"

python manage.py makemigrations --noinput
python manage.py migrate --noinput

python manage.py collectstatic --noinput

exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
