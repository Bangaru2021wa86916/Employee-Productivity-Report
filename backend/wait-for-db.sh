#!/bin/sh
set -e

# Default host if not provided
MYSQL_HOST="${MYSQL_HOST:-db}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

echo "⏳ Waiting for MySQL to be ready at ${MYSQL_HOST}:${MYSQL_PORT}..."
# Use nc to check port
until nc -z "$MYSQL_HOST" "$MYSQL_PORT"; do
  sleep 2
  echo "Still waiting for MySQL..."
done

echo "✅ MySQL is up - starting Flask..."
exec python app.py
