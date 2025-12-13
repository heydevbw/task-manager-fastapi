from typing import List, Optional
from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task Manager API",
    description="Simple, interactive Task Manager backend built with FastAPI.",
    version="1.0.0",
)

# ---------- Pydantic models (request/response schemas) ----------

class TaskBase(BaseModel):
    title: str = Field(..., example="Prepare sprint demo")
    description: Optional[str] = Field(
        None, example="Create slides and demo for the client meeting"
    )
    status: str = Field(
        "todo",
        description="Task status: todo, in_progress, done",
        example="in_progress",
    )
    due_date: Optional[date] = Field(None, example="2025-12-31")
    assignee: Optional[str] = Field(None, example="bharat@company.com")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, example="Update sprint demo")
    description: Optional[str] = None
    status: Optional[str] = Field(
        None, description="Task status: todo, in_progress, done"
    )
    due_date: Optional[date] = None
    assignee: Optional[str] = None


class Task(TaskBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ---------- In‑memory storage (for now; later you’ll use a DB) ----------

tasks_db: dict[int, Task] = {}
current_id = 0


def get_next_id() -> int:
    global current_id
    current_id += 1
    return current_id


# ---------- Routes ----------

@app.get("/", summary="API health check")
def read_root():
    return {"message": "Task Manager API is running"}


@app.get("/tasks", response_model=List[Task], summary="List all tasks")
def list_tasks():
    return list(tasks_db.values())


@app.post(
    "/tasks",
    response_model=Task,
    status_code=201,
    summary="Create a new task",
)
def create_task(task_in: TaskCreate):
    task_id = get_next_id()
    task = Task(
        id=task_id,
        created_at=datetime.utcnow(),
        **task_in.dict(),
    )
    tasks_db[task_id] = task
    return task


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get a task by ID",
)
def get_task(task_id: int):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task",
)
def update_task(task_id: int, task_update: TaskUpdate):
    stored_task = tasks_db.get(task_id)
    if not stored_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.dict(exclude_unset=True)
    updated_task_data = stored_task.dict()
    updated_task_data.update(update_data)

    updated_task = Task(**updated_task_data)
    tasks_db[task_id] = updated_task
    return updated_task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
)
def delete_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks_db[task_id]
