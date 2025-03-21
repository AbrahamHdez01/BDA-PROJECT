#!/bin/sh

# Wait for the database to be ready
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Import default data if needed
if [ "$LOAD_SAMPLE_DATA" = "true" ]; then
    echo "Loading sample data..."
    python manage.py import_sample_data
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
