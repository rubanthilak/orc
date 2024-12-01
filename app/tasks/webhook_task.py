from app.services.task_service import execute_task
from app.celery import scheduler

@scheduler.task  
def webhook(task_id: str):  
    execute_task(task_id)
    