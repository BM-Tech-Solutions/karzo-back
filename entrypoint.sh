#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
import psycopg2
import os

host = os.environ.get('POSTGRES_HOST', 'db')
port = os.environ.get('POSTGRES_PORT', '5432')
user = os.environ.get('POSTGRES_USER', 'postgres')
password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
dbname = os.environ.get('POSTGRES_DB', 'postgres')

while True:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        conn.close()
        break
    except psycopg2.OperationalError:
        print('Database not ready yet, waiting...')
        time.sleep(1)
"
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head



# Start the application
echo "Starting application..."
exec "$@"
