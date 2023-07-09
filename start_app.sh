#!/bin/bash
# do migrations
gunicorn --bind 0.0.0.0:8000 recoleccion.wsgi:application