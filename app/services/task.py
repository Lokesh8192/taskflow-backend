from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.task import Task
from app.schemas.project_member import ProjectRole
from app.schemas.task import TaskCreate, TaskUpdate
from app.models.task_history import TaskHistory
from app.schemas.task_history import TaskHistoryResponse


def get_project_membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    statement = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    return db.scalar(statement)


def get_project_or_rise(db: Session, project_id: int) -> Project:
    project = db.scalar(select(Project).where(
        Project.project_id == project_id))
    if project is None:
        raise ValueError("Project not found")
    return project


def validate_project_member(db: Session, project_id: int, user_id: int) -> ProjectMember:
    project = get_project_or_rise(db, project_id)
    if project.created_by == user_id:
        return ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=ProjectRole.OWNER.value,
        )
    membership = get_project_membership(db, project_id, user_id)
    if membership is None:
        raise PermissionError("User isn't a member of this project")
    return membership


def validate_assignee(db: Session, project_id: int, assigned_to: int | None) -> None:
    if assigned_to is None:
        return
    membership = get_project_membership(db, project_id, assigned_to)
    if membership is None:
        raise ValueError("Assigned user must be member os this project")
    user = db.scalar(select(User).where(User.id == assigned_to))
    if user is None:
        raise ValueError("Assigned use rnot found")
    if not user.is_active:
        raise ValueError("Assigned user account is inactive")


def create_tasks(db: Session, data: TaskCreate, current_user: User) -> Task:
    get_project_or_rise(db, data.project_id)
    membership = validate_project_member(db, data.project_id, current_user.id)
    if membership.role == ProjectRole.VIEWER.value:
        raise PermissionError("Viewers can't create tasks")
    validate_assignee(db, data.project_id, data.assigned_to)
    title = data.title.strip()
    if not title:
        raise ValueError("Task title can't be empty")
    task = Task(project_id=data.project_id, title=title, description=(data.description.strip() if data.description else None),
                status=data.status.value,
                priority=data.priority.value,
                due_date=data.due_date,
                created_by=current_user.id,
                assigned_to=data.assigned_to
                )

    db.add(task)
    db.flush()

    history = TaskHistory(
        task_id=task.task_id,
        changed_by=current_user.id,
        action="CREATED",
        old_status=None,
        new_status=task.status,
        old_priority=None,
        new_priority=task.priority,
        old_assigned_to=None,
        new_assigned_to=task.assigned_to,
    )

    db.add(history)

    try:
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise
    return task


def get_project_tasks(db: Session, project_id: int, current_user: User, status: str | None = None, priority: str | None = None, assigned_to: int | None = None) -> list[Task]:
    get_project_or_rise(db, project_id)
    validate_project_member(db, project_id, current_user.id)
    statement = select(Task).where(
        Task.project_id == project_id
    )
    if status is not None:
        statement = statement.where(
            Task.status == status
        )

    if priority is not None:
        statement = statement.where(
            Task.priority == priority
        )

    if assigned_to is not None:
        statement = statement.where(
            Task.assigned_to == assigned_to
        )
    statement = statement.order_by(
        Task.task_id.desc()
    )

    return list(db.scalars(statement).all())


def get_task(db: Session, task_id: int, current_user: User) -> Task:
    task = db.scalar(select(Task).where(Task.task_id == task_id))
    if task is None:
        raise ValueError("Task not found")
    validate_project_member(db, task.project_id, current_user.id)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate, current_user: User) -> Task:
    task = get_task(db, task_id, current_user)
    membership = validate_project_member(db, task.project_id, current_user.id)
    is_manager = membership.role in (
        ProjectRole.OWNER.value, ProjectRole.MANAGER.value)
    is_creator = task.created_by == current_user.id
    if not is_manager and not is_creator:
        raise PermissionError("You don't have permission to update this task")
    old_status = task.status
    old_priority = task.priority
    old_assigned_to = task.assigned_to
    updates = data.model_dump(exclude_unset=True)
    if "title" in updates:
        title = updates["title"]
        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("Task title can't be empty")
            task.title = title
    if "description" in updates:
        description = updates["description"]

        task.description = (
            description.strip()
            if description
            else None
        )

    if "status" in updates:
        task.status = updates["status"].value

    if "priority" in updates:
        task.priority = updates["priority"].value

    if "due_date" in updates:
        task.due_date = updates["due_date"]

    if "assigned_to" in updates:
        assigned_to = updates["assigned_to"]

        validate_assignee(
            db,
            task.project_id,
            assigned_to,
        )

        task.assigned_to = assigned_to
    status_changed = task.status != old_status
    priority_changed = task.priority != old_priority
    assignment_changed = (
        task.assigned_to != old_assigned_to
    )

    if (
        status_changed
        or priority_changed
        or assignment_changed
    ):
        history = TaskHistory(
            task_id=task.task_id,
            changed_by=current_user.id,
            action="UPDATED",
            old_status=(
                old_status
                if status_changed
                else None
            ),
            new_status=(
                task.status
                if status_changed
                else None
            ),
            old_priority=(
                old_priority
                if priority_changed
                else None
            ),
            new_priority=(
                task.priority
                if priority_changed
                else None
            ),
            old_assigned_to=(
                old_assigned_to
                if assignment_changed
                else None
            ),
            new_assigned_to=(
                task.assigned_to
                if assignment_changed
                else None
            ),
        )

        db.add(history)

    try:
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    return task


def delete_task(
    db: Session,
    task_id: int,
    current_user: User,
) -> None:
    task = get_task(
        db,
        task_id,
        current_user,
    )

    membership = validate_project_member(
        db,
        task.project_id,
        current_user.id,
    )

    is_manager = membership.role in {
        ProjectRole.OWNER.value,
        ProjectRole.MANAGER.value,
    }

    is_creator = task.created_by == current_user.id

    if not is_manager and not is_creator:
        raise PermissionError(
            "You do not have permission to delete this task"
        )

    db.delete(task)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
def get_task_history(db:Session,task_id:int,current_user:User)->list[TaskHistory]:
    get_task(db,task_id,current_user)
    statement=(select(TaskHistory).where(TaskHistory.task_id==task_id).order_by(TaskHistory.id.desc()))
    return list(db.scalars(statement).all())
