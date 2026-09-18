from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AssignableProjectRole(str, Enum):
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMemberCreate(BaseModel):
    user_id: int = Field(
        gt=0, description="Id of the user to add to the project")
    role: AssignableProjectRole=AssignableProjectRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    role:AssignableProjectRole


class ProjectMemberResponse(BaseModel):
    member_id: int
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )
