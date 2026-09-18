from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=APIResponse[UserResponse])
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "message": "User profile retrieved successfully",
        "data": current_user
    }
