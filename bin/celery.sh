#!/usr/bin/env bash
python -m celery -A app.celery.scheduler beat --loglevel=info
