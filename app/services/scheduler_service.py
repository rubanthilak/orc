import requests
import json
from app.celery import scheduler
from celery.schedules import crontab
from sqlalchemy.orm import Session
from db.client import SessionLocal
from app.models.task import Task
from app.models.result import TaskResult
from datetime import datetime

# Task to trigger webhooks and save the result to the database
def execute_task(task_id: str):
    db: Session = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        db.close()
        return

    webhook = task.webhook_url
    headers = json.loads(task.headers) if task.headers else {}

    try:
        response = requests.post(webhook, json=json.loads(task.data), headers=headers)
        save_task_result(db, task_id, response)
        db.commit()
        return {"status": "success", "response_code": response.status_code}
    except Exception as e:
        save_task_result(db, task_id, None, error=str(e))
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def save_task_result(db: Session, task_id: str, response=None, error=None):
    """Save the result of task execution to the database."""
    task_result = TaskResult(
        task_id=task_id,
        status_code=response.status_code if response else None,
        response_body=response.text if response else None,
        headers=json.dumps(dict(response.headers)) if response else None,
        error=error,
        executed_at=datetime.utcnow(),
    )
    db.add(task_result)

def schedule_task(task_data: dict):
    """Schedule a task based on task_data either as a one-time or recurring task."""
    task_id = task_data["task_id"]
    scheduled_time = task_data["scheduled_time"]
    recurring = task_data.get("recurring")

    if recurring:
        cron = recurring["cron"]
        timezone = recurring.get("timezone", "UTC")
        scheduler.add_periodic_task(
            crontab.from_string(cron),
            execute_task.s(task_id),
            name=f"cron_{task_id}",
            options={"expires": None}
        )
    else:
        execute_task.apply_async((task_id,), eta=datetime.fromisoformat(scheduled_time))

def delete_scheduled_task(task_id: str, is_recurring: bool = False):
    """Remove a scheduled task from Celery Beat or revoke a one-time task."""
    if is_recurring:
        revoke_recurring_task(f"cron_{task_id}")
    else:
        scheduler.control.revoke(task_id, terminate=True)

def revoke_recurring_task(task_name: str):
    """Revoke a recurring task by its name."""
    from celery import current_app
    beat_schedule = current_app.control.inspect().scheduled()

    if beat_schedule:
        for worker, tasks in beat_schedule.items():
            for task in tasks:
                if task["name"] == task_name:
                    scheduler.control.revoke(task["id"], terminate=True)
                    print(f"Recurring task '{task_name}' revoked.")
