from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskPriority, TaskStatus, TaskUpdate
from app.schemas.task_history import TaskHistoryResponse
from app.services.task import create_tasks, get_project_tasks, get_task, update_task, delete_task, get_task_history

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=APIResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        task = create_tasks(
            db,
            data,
            current_user,
        )

        return {
            "status": "success",
            "message": "Task created successfully",
            "data": task,
        }

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        detail = str(exc)

        if detail == "Project not found":
            response_status = status.HTTP_404_NOT_FOUND
        else:
            response_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=response_status,
            detail=detail,
        ) from exc


@router.get("/{task_id}/history", response_model=APIResponse[list[TaskHistoryResponse]])
def get_task_history_by_id(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        history = get_task_history(db, task_id, current_user)
        return {
            "status": "success",
            "message": "Task history retrieved successfully",
            "data": history,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
def get_task_by_id(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        task = get_task(db, task_id, current_user)
        return {
            "status": "success",
            "message": "Task retrieved successfully",
            "data": task,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "",
    response_model=APIResponse[list[TaskResponse]],
)
def list_tasks(
    project_id: int = Query(
        gt=0,
        description="ID of the project",
    ),
    task_status: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Filter tasks by status",
    ),
    priority: TaskPriority | None = Query(
        default=None,
        description="Filter tasks by priority",
    ),
    assigned_to: int | None = Query(
        default=None,
        gt=0,
        description="Filter tasks by assigned user ID",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        tasks = get_project_tasks(
            db=db,
            project_id=project_id,
            current_user=current_user,
            status=(
                task_status.value
                if task_status is not None
                else None
            ),
            priority=(
                priority.value
                if priority is not None
                else None
            ),
            assigned_to=assigned_to,
        )

        return {
            "status": "success",
            "message": "Tasks retrieved successfully",
            "data": tasks,
        }

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
def update_task_by_id(task_id: int, data: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        task = update_task(db, task_id, data, current_user)
        return {
            "status": "success",
            "message": "Task updated successfully",
            "data": task,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if str(exc) == "Task not found"
            else status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{task_id}", response_model=APIResponse[None])
def delete_task_by_id(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        delete_task(db, task_id, current_user)
        return {
            "status": "success",
            "message": "Task deleted successfully",
            "data": None,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if str(exc) == "Task not found"
            else status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
