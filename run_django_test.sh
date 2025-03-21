#!/bin/sh

# Make the script executable
chmod +x entrypoint.sh

# Run Django development server without database dependency
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
