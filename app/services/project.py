from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.project_member import ProjectRole


def _is_project_accessible(db: Session, project: Project, user_id: int) -> bool:
    if project.created_by == user_id:
        return True
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return membership is not None


def create_project(db: Session, data: ProjectCreate, current_user: User) -> Project:
    project = Project(project_name=data.name.strip(), description=(
        data.description.strip() if data.description else None), created_by=current_user.id)
    db.add(project)
    db.flush()
    # Add creator as project owner.
    member = ProjectMember(project_id=project.project_id,
                           user_id=current_user.id, role="owner")
    db.add(member)
    db.commit()
    db.refresh(project)

    return project


def get_user_projects(db: Session, current_user: User) -> list[Project]:
    statement = (
        select(Project)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.project_id)
        .where(
            (Project.created_by == current_user.id)
            | (ProjectMember.user_id == current_user.id)
        )
        .order_by(Project.project_id.desc())
        .distinct()
    )
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: int, current_user: User) -> Project:
    project = db.scalar(select(Project).where(Project.project_id == project_id))
    if project is None:
        raise ValueError("Project not found or access denied")
    if not _is_project_accessible(db, project, current_user.id):
        raise ValueError("Project not found or access denied")
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate, current_user: User) -> Project:
    project = get_project(db, project_id, current_user)
    if project.created_by != current_user.id:
        raise PermissionError("Only project owner can update the project")
    if data.name is not None:
        project.project_name = data.name.strip()
    if data.description is not None:
        project.description = data.description.strip()
    db.commit()
    db.refresh(project)
    return project
def delete_project(
    db: Session,
    project_id: int,
    current_user: User,
) -> None:
    project = get_project(
        db,
        project_id,
        current_user,
    )

    if project.created_by != current_user.id:
        raise PermissionError(
            "Only the project owner can delete the project"
        )

    db.delete(project)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

def get_project_member(db: Session, user_id: int, project_id: int) -> ProjectMember | None:
    statement = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    return db.scalar(statement)


def add_project_member(db: Session, project_id: int, user_id: int, role: str, current_user: User) -> ProjectMember:
    project = get_project(db, project_id, current_user)
    if project.created_by != current_user.id:
        raise PermissionError("Only Project owner can add members")
    if role == ProjectRole.OWNER:
        raise ValueError("New can't be assigned the owner role")
    user_statement = select(User).where(User.id == user_id)
    user = db.scalar(user_statement)
    if user is None:
        raise ValueError("User not found")
    existing_member = get_project_member(db, user_id, project_id)
    if existing_member:
        raise ValueError("User is already a project member")
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role.value)
    db.add(member)
    try:
        db.commit()
        db.refresh(member)
    except Exception:
        db.rollback()
        raise
    return member


def list_project_members(db: Session, project_id: int, current_user: User) -> list[ProjectMember]:
    get_project(db, project_id, current_user)
    statement = (select(ProjectMember).where(
        ProjectMember.project_id == project_id).order_by(ProjectMember.member_id))
    return list(db.scalars(statement).all())


def update_project_member(db: Session, project_id: int, user_id: int, role: str, current_user: User) -> ProjectMember:
    project = get_project(db, project_id, current_user)
    if project.created_by != current_user.id:
        raise PermissionError("only project owner can update members")
    if role == ProjectRole.OWNER:
        raise ValueError("member role can't be changed to owner")
    member = get_project_member(db, user_id, project_id)
    if member is None:
        raise ValueError("Project member not found")
    if member.user_id == project.created_by:
        raise ValueError("The Project owner's role can't be changed")
    member.role = role.value
    db.commit()
    db.refresh(member)
    return member


def remove_project_member(db: Session, project_id: int, user_id: int, current_user: User) -> None:
    project = get_project(db, project_id, current_user)
    if project.created_by != current_user.id:
        raise PermissionError("Only project owner can remove the member")
    if user_id == project.created_by:
        raise ValueError("Project owner can't be removed")
    member = get_project_member(db, user_id, project_id)
    if member is None:
        raise ValueError("Project member not found")
    db.delete(member)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
