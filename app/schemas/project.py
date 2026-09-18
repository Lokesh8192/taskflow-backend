from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ProjectResponse(BaseModel):
    id: int = Field(validation_alias=AliasChoices("id", "project_id"), serialization_alias="id")
    name: str = Field(validation_alias=AliasChoices("name", "project_name"), serialization_alias="name")
    description: str | None
    created_by: int
    updated_at: datetime

    @computed_field
    @property
    def project_id(self) -> int:
        return self.id

    model_config = ConfigDict(
        from_attributes=True,
    )
