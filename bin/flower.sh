#!/usr/bin/env bash
python -m celery -A bg.main.scheduler flower --port=4000 --loglevel=debug 
