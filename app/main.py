from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.core.exception_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging(settings.LOG_LEVEL)

openapi_tags = [
    {
        "name": "Authentication",
        "description": (
            "User registration, login, token refresh, and logout."
        ),
    },
    {
        "name": "Users",
        "description": (
            "Authenticated user profile and user-related operations."
        ),
    },
    {
        "name": "Admin",
        "description": (
            "System administrator-only operations."
        ),
    },
    {
        "name": "Projects",
        "description": (
            "Create and manage projects and project membership."
        ),
    },
    {
        "name": "Tasks",
        "description": (
            "Create, retrieve, update, delete, filter, "
            "and audit project tasks."
        ),
    },
]


app = FastAPI(
    title="TaskFlow API",
    description=(
        "A backend REST API for task management and collaboration. "
        "The API provides JWT authentication, role-based access control, "
        "project membership, task management, filtering, and task history."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)


# Global exception handlers
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)


# API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(tasks_router)


@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Returns the basic status of the TaskFlow API.",
)
def root():
    return {
        "status": "success",
        "message": "TaskFlow API is running",
        "data": None,
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Checks whether the TaskFlow API is running.",
)
def health_check():
    return {
        "status": "success",
        "message": "TaskFlow API is healthy",
        "data": None,
    }