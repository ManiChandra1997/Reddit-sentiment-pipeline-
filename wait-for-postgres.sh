#!/bin/bash
# wait-for-postgres.sh

set -e

host="postgres"
user="postgres"

until pg_isready -h "$host" -U "$user"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

>&2 echo "Postgres is up - executing command"
exec "$@"