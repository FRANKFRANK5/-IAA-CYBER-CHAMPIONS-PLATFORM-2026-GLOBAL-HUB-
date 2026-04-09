#!/bin/bash
set -euo pipefail

# Mpangilio wa msingi (Defaults)
WORKERS=${WORKERS:-1}
WORKER_CLASS=${WORKER_CLASS:-gevent}
ACCESS_LOG=${ACCESS_LOG:--}
ERROR_LOG=${ERROR_LOG:--}
WORKER_TEMP_DIR=${WORKER_TEMP_DIR:-/dev/shm}
SECRET_KEY=${SECRET_KEY:-}
SKIP_DB_PING=${SKIP_DB_PING:-false}

# 1. USALAMA: Angalia Secret Key
# Kama una workers wengi, sessions lazima ziwe signed kwa key moja inayofanana
if [ ! -f .ctfd_secret_key ] && [ -z "$SECRET_KEY" ]; then
    if [ "$WORKERS" -gt 1 ]; then
        echo "----------------------------------------------------------------------"
        echo "[ ERROR ] You are configured to use more than 1 worker ($WORKERS)."
        echo "[ ERROR ] To do this, you must define the SECRET_KEY environment variable."
        echo "[ ERROR ] Tip: Generate one using: python -c 'import os; print(os.urandom(16).hex())'"
        echo "----------------------------------------------------------------------"
        exit 1
    fi
fi

# 2. DATABASE PING: Hakikisha MySQL/MariaDB imeshawaka kabisa
if [[ "$SKIP_DB_PING" == "false" ]]; then
  echo "Checking database connection..."
  # Tunatumia python ping.py iliyopo ndani ya CTFd
  python ping.py
fi

# 3. DATABASE UPGRADE: Tengeneza au sasisha table za database
echo "Running database migrations (flask db upgrade)..."
flask db upgrade

# 4. START GUNICORN: Washa injini ya CTFd
echo "Starting CTFd with $WORKERS workers..."
exec gunicorn 'CTFd:create_app()' \
    --bind '0.0.0.0:8000' \
    --workers "$WORKERS" \
    --worker-tmp-dir "$WORKER_TEMP_DIR" \
    --worker-class "$WORKER_CLASS" \
    --access-logfile "$ACCESS_LOG" \
    --error-logfile "$ERROR_LOG"