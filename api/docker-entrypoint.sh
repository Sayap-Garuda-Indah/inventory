#!/bin/sh
set -e

python scripts/migrate.py upgrade
python scripts/create_admin.py
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
