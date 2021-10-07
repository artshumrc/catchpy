#!/bin/bash

set -o errexit
set -o pipefail

until python3 /scripts/postgres_ready.py; do
  >&2 echo "Waiting for PostgreSQL to become available..."
  sleep 1
done
>&2 echo "PostgreSQL is available"

nginx

if [[ $WAITRESS ]]
then
  if [ "$WAITRESS" = "True" ]; then
    python3 manage.py waitress --port=5000 --threads=16
  else
    python3 manage.py runserver 5000
  fi
else
   python3 manage.py runserver 5000
fi
