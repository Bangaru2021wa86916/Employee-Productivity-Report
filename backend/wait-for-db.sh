#!/bin/sh
set -e

echo "⏳ Waiting for MySQL to be ready at $MYSQL_HOST:3306..."
until nc -z "$MYSQL_HOST" 3306; do
  sleep 2
  echo "Still waiting for MySQL..."
done

echo "✅ MySQL is up - starting Flask..."
exec python app.py
