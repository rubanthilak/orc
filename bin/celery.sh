#!/usr/bin/env bash
python3 -m celery -A app.celery.scheduler beat --loglevel=info
