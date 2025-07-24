#!/bin/sh
set -e

# Set default credentials (not secure)
DJANGO_SUPERUSER_USERNAME=admin-snow
DJANGO_SUPERUSER_EMAIL=snowflake.2k04@gmail.com
DJANGO_SUPERUSER_PASSWORD=Snow@2004


# Run Django migrations
python manage.py migrate --noinput

# Collect static files into the STATIC_ROOT directory
python manage.py collectstatic --noinput


# Create a superuser with the specified username and password
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
"

# Start the app using Gunicorn and the WSGI server
exec gunicorn --bind 0.0.0.0:8004 ai_query_agent.wsgi:application
