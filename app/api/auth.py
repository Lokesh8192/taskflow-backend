from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.schemas.response import APIResponse
from app.schemas.auth import LoginResponse, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.services.user import create_user, authenticate_user, refresh_access_token, revoke_refresh_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, data)
        return {
            "status": "success",
            "message": "User registered successfully",
            "data": user
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc),) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Username already exists") from exc


@router.post("/login", response_model=APIResponse[LoginResponse])
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    try:
        access_token, refresh_token, user = authenticate_user(db, data)
        return {
            "status": "success",
            "message": "User logged in successfully",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            },
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


@router.post("/refresh", response_model=APIResponse[TokenResponse])
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        access_token = refresh_access_token(db, data.refresh_token)
        return {
            "status": "success",
            "message": "Access token refreshed successfully",
            "data": {
                "access_token": access_token,
                "refresh_token": data.refresh_token,
                "token_type": "bearer",
            },
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc), headers={"WWW-Authenticate": "Bearer"},) from exc


@router.post("/logout", response_model=APIResponse[None])
def logout_user(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        revoke_refresh_token(db, data.refresh_token)
        return {
            "status": "success",
            "message": "User logged out successfully",
            "data": None,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
