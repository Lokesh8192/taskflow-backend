from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    changed_by: int
    action: str
    old_status: str | None
    new_status: str | None
    old_priority: str | None
    new_priority: str | None
    old_assigned_to: str | None
    new_assigned_to: str | None
    changed_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
