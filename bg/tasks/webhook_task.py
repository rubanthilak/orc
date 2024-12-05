from app.services.scheduler_service import execute_task
from bg.celery import scheduler

@scheduler.task(rate_limit="10/m")  
def webhook(task_id: str):  
    execute_task(task_id)
    