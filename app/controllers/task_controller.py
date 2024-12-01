# app/controllers/task_controller.py

from app.schemas.task_schema import TaskSchema
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.client import client
from app.services import task_service as TaskService

router = APIRouter()

@router.get("/")
async def list_tasks_route(db: Session = Depends(client)):
    return TaskService.list(db)

@router.post("/", status_code=201)
async def create_task_route(data: TaskSchema, db: Session = Depends(client)):
    return TaskService.create(db, data)

@router.put("/{task_id}")
async def edit_task_route(task_id: str, data: TaskSchema, db: Session = Depends(client)):
    return TaskService.update(db, task_id, data)

@router.delete("/{task_id}")
async def delete_task_route(task_id: str, db: Session = Depends(client)):
    return TaskService.destroy(db, task_id)

@router.get("/{task_id}/results")
async def get_task_results_route(task_id: str, db: Session = Depends(client)):
    return TaskService.results(db, task_id)
