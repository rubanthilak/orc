import os
from celery import Celery
from config.environment import init

# Initialize environment variables
init()

# Retrieve the DATABASE_URL from environment variables
REDIS_URL = os.getenv("REDIS_URL")

# Create a Celery instance
scheduler = Celery("scheduler", broker=REDIS_URL)
