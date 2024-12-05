#!/usr/bin/env bash
python -m celery -A app.celery.scheduler flower --port=4000 beat --loglevel=info 
