#!/bin/bash
# do migrations
python manage.py migrate
gunicorn --bind 0.0.0.0:8000 recoleccion.wsgi:application