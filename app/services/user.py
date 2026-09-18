from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.config import settings


def create_user(
    db: Session,
    data: UserCreate,
) -> User:
    username = data.username.strip()
    email = data.email.lower().strip()

    statement = select(User).where(
        or_(
            User.username == username,
            User.email == email,
        )
    )

    existing_user = db.scalar(statement)

    if existing_user:
        if existing_user.username == username:
            raise ValueError("Username already exists")

        raise ValueError("Email already exists")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(data.password),
        role="user",
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def authenticate_user(
    db: Session,
    data: UserLogin,
) -> tuple[str, str, User]:
    email = data.email.lower().strip()

    statement = select(User).where(
        User.email == email
    )

    user = db.scalar(statement)

    if user is None:
        raise ValueError("Invalid email or password")

    if not verify_password(
        data.password,
        user.hashed_password,
    ):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("User account is inactive")

    access_token = create_access_token(
        str(user.id)
    )

    refresh_token = create_refresh_token(
        str(user.id)
    )
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        ),
        is_revoked=False,
    )

    db.add(refresh_token_record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return access_token, refresh_token, user


def refresh_access_token(db: Session, refresh_token: str) -> str:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh tokens")
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Invalid refresh tokens")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invaild refresh token") from exc
    statement = select(RefreshToken).where(RefreshToken.token == refresh_token,
                                           RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
    session = db.scalar(statement)
    if session is None:
        raise ValueError("Refreshtoken has been revoked or does not exist")
    now = datetime.now(timezone.utc)
    if session.expires_at <= now:
        raise ValueError("Refresh token has expired")
    user_statement = select(User).where(User.id == user_id)
    user = db.scalar(user_statement)
    if user is None:
        raise ValueError("User not found")
    if not user.is_active:
        raise ValueError("User account is inactive")
    return create_access_token(str(user.id))


def revoke_refresh_token(
    db: Session,
    refresh_token: str,
) -> None:
    statement = select(RefreshToken).where(
        RefreshToken.token == refresh_token,
        RefreshToken.is_revoked.is_(False),
    )

    session = db.scalar(statement)

    if session is None:
        raise ValueError("Refresh token not found")

    session.is_revoked = True
    session.revoked_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
