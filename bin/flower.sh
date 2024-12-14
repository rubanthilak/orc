#!/usr/bin/env bash
python -m celery -A bg.main.scheduler flower --broker=redis://localhost:6379/0 --broker_api=redis://localhost:6379/0 --port=4000 
