from bg.celery import scheduler
from celery.schedules import crontab
from datetime import datetime, timedelta, timezone

def enqueue(task: callable, kwargs: dict, scheduled_time: str = None, cron: str = None):
    """Add a scheduled task to Celery Beat."""
    task_id = kwargs["task_id"]
    scheduled_time = scheduled_time if scheduled_time != None else (datetime.now() + timedelta(minutes=5)).isoformat()
    if cron != None:
        scheduler.add_periodic_task(
            crontab(cron), 
            task.s(**kwargs), 
            f"cron_{task.__name__}_{task_id}"
        )
    else:
        scheduler.add_periodic_task(
            datetime.fromisoformat(scheduled_time).replace(tzinfo=timezone.utc),
            task.s(**kwargs), 
            f"{task.__name__}_{task_id}"
        )
    
def dequeue(task_name: str, task_id: str, is_recurring: bool = False):
    """Remove a scheduled task from Celery Beat or revoke a one-time task."""
    if is_recurring:
        dequeue_recurring_task(f"cron_{task_name}_{task_id}")
    else:
        scheduler.control.revoke(f"{task_name}_{task_id}", terminate=True)

def dequeue_recurring_task(task_name: str):
    """Revoke a recurring task by its name."""
    beat_schedule = scheduler.control.inspect().scheduled()

    if beat_schedule:
        for _worker, tasks in beat_schedule.items():
            for task in tasks:
                if task["name"] == task_name:
                    scheduler.control.revoke(task["id"], terminate=True)
                    print(f"Recurring task '{task_name}' revoked.")

from celery import signature

def schedule_task(task, args, scheduled_time=None, cron_string=None):
    """
    Schedule a task to run at a specified time or with a cron string.

    Args:
        task (str): The name of the task to schedule.
        args (tuple): The arguments to pass to the task.
        scheduled_time (datetime, optional): The time to schedule the task to run. Defaults to None.
        cron_string (str, optional): The cron string to use to schedule the task. Defaults to None.

    Returns:
        None

    Usage:
  
        from datetime import datetime

        app = Celery('tasks', broker='amqp://guest@localhost//')
        task_name = 'my_task'
        args = (1, 2, 3)
        scheduled_time = datetime(2023, 3, 15, 14, 30)  # March 15, 2023 at 2:30 PM
        cron_string = '0 8 * * *'  # Run every day at 8am

        schedule_task(app, task_name, args, scheduled_time, cron_string)
    """
    if cron_string:
        # Use the cron string to schedule the task
        scheduler.add_periodic_task(crontab(cron_string), task, args=args)
    elif scheduled_time:
        # Use the scheduled time to schedule the task
        scheduler.add_periodic_task(scheduled_time, task, args=args)
    else:
        # Enqueue the task after 5 minutes if no scheduled time or cron string is provided
        enqueue_time = datetime.now() + timedelta(seconds=10)
        scheduler.add_periodic_task(enqueue_time, signature(task, args=args), name=task)