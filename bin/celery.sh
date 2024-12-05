#!/usr/bin/env bash
python -m celery -A bg.main.scheduler worker --beat --loglevel=debug 
