from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50,
                          description="Unique UserName")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Username is required")

        if " " in value:
            raise ValueError("Username must not contain spaces")

        if not value.replace("_", "").isalnum():
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be empty")

        if not any(char.isupper() for char in value):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not any(char.islower() for char in value):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one number"
            )

        if not any(not char.isalnum() for char in value):
            raise ValueError(
                "Password must contain at least one special character"
            )

        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int = Field(validation_alias=AliasChoices("id", "user_id"), serialization_alias="id")
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    @computed_field
    @property
    def user_id(self) -> int:
        return self.id

    model_config = ConfigDict(from_attributes=True)
