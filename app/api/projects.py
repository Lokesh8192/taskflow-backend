from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberResponse, ProjectMemberUpdate
from app.services.project import create_project, update_project, get_project, get_user_projects, get_project_member, list_project_members, add_project_member, update_project_member, remove_project_member, delete_project
from app.schemas.response import APIResponse

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

@router.post("", response_model=APIResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
def project_create(data: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        project = create_project(db, data, current_user)
        return {
            "status": "success",
            "message": "Project created successfully",
            "data": project,
        }
    except Exception:
        db.rollback()
        raise


@router.get("", response_model=APIResponse[list[ProjectResponse]])
def projects_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = get_user_projects(db, current_user)
    return {
        "status": "success",
        "message": "Projects retrieved successfully",
        "data": projects,
    }


@router.get("/{project_id}", response_model=APIResponse[ProjectResponse])
def get_one_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        project = get_project(db, project_id, current_user)
        return {
            "status": "success",
            "message": "Project retrieved successfully",
            "data": project,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{project_id}", response_model=APIResponse[ProjectResponse])
def update_project_by_id(project_id: int, data: ProjectUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        project = update_project(db, project_id, data, current_user)
        return {
            "status": "success",
            "message": "Project updated successfully",
            "data": project,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{project_id}",
    response_model=APIResponse[None],
)
def delete_project_by_id(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        delete_project(
            db,
            project_id,
            current_user,
        )

        return {
            "status": "success",
            "message": "Project deleted successfully",
            "data": None,
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


@router.post(
    "/{project_id}/members",
    response_model=APIResponse[ProjectMemberResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_member(project_id: int, data: ProjectMemberCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        member = add_project_member(
            db, project_id, data.user_id, data.role, current_user)
        return {
            "status": "success",
            "message": "Project member added successfully",
            "data": member,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code_value = (
            status.HTTP_404_NOT_FOUND
            if detail == "User not found"
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code_value,
            detail=detail,
        ) from exc


@router.get("/{project_id}/members", response_model=APIResponse[list[ProjectMemberResponse]])
def get_members(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        members = list_project_members(db, project_id, current_user)
        return {
            "status": "success",
            "message": "Project members retrieved successfully",
            "data": members,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{project_id}/members/{user_id}", response_model=APIResponse[ProjectMemberResponse])
def update_member(project_id: int, user_id: int, data: ProjectMemberUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        member = update_project_member(
            db, project_id, user_id, data.role, current_user)
        return {
            "status": "success",
            "message": "Project member updated successfully",
            "data": member,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{project_id}/members/{user_id}", response_model=APIResponse[None])
def delete_member(project_id: int, user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        remove_project_member(db, project_id, user_id, current_user)
        return {
            "status": "success",
            "message": "Project member removed successfully",
            "data": None,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
