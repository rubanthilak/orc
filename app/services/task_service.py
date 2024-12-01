import json
from app.models.webhook import Webhook
from app.schemas.task_schema import TaskSchema
import requests
from app.celery import scheduler
from celery.schedules import crontab
from sqlalchemy.orm import Session
from db.client import SessionLocal
from app.models.task import Task
from app.models.result import TaskResult
from datetime import datetime

def create(db: Session, data: TaskSchema):
    """Create and schedule a new task."""
    try:
        task_data = data.model_dump()
        webhook_data = task_data.pop("webhook", None)

        if webhook_data:
            webhook = Webhook(**webhook_data)
            task_data["webhook"] = webhook

        task = Task(**task_data)
        db.add(task)
        db.commit()
        schedule_task(task_data, db)
        return {"status": "success", "message": "Task created and scheduled successfully"}
    finally:
        db.close()

def update(db: Session, task_id: str, updated_data: dict):
    """Edit an existing task and update its schedule."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        return {"status": "error", "message": "Task not found"}

    for key, value in updated_data.items():
        setattr(task, key, value)

    db.commit()
    delete_scheduled_task(task_id, is_recurring=bool(task.recurring_cron))
    schedule_task(updated_data, db)
    return {"status": "success", "message": "Task updated and rescheduled"}

def destroy(db: Session, task_id: str, is_recurring: bool = False):
    """Delete a task and remove its schedule."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        db.close()
        return {"status": "error", "message": "Task not found"}

    db.delete(task)
    db.commit()
    db.close()
    delete_scheduled_task(task_id, is_recurring)
    return {"status": "success", "message": "Task deleted"}

def list(db: Session):
    """List all tasks."""
    tasks = db.query(Task).all()
    db.close()
    return [task.to_dict() for task in tasks]

def results(db: Session, task_id: str):
    """Retrieve all execution results for a given task."""
    results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
    db.close()
    return [result.to_dict() for result in results]

# Task to trigger webhooks and save the result to the database
def execute_task(task_id: str):
    db: Session = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        db.close()
        return {"status": "error", "message": "Task not found"}

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
