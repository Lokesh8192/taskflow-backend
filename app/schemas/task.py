from datetime import datetime, date
from enum import Enum
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCreate(BaseModel):
    project_id: int = Field(gt=0, description="Id of the project")
    title: str = Field(min_length=3, max_length=200, description="Task title")
    description: str | None = Field(
        default=None, max_length=2000, description="Task Description")
    status: TaskStatus = Field(
        default=TaskStatus.TODO, description="Task Status")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Task Priority")
    due_date: date | None = Field(default=None, description="Task due date")
    assigned_to: int | None = Field(
        default=None, gt=0, description="Project member assigned to task")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assigned_to: int | None = Field(default=None, gt=0,)


class TaskResponse(BaseModel):
    id: int = Field(validation_alias=AliasChoices("id", "task_id"), serialization_alias="id")
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def task_id(self) -> int:
        return self.id

    model_config = ConfigDict(
        from_attributes=True,
    )
