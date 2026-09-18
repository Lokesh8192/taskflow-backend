from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.schemas.response import APIResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

@router.get("/dashboard", response_model=APIResponse[dict])
def admin_dashboard(current_admin: User = Depends(get_current_admin)):
    return {
        "status": "success",
        "message": "Admin dashboard accessed successfully",
        "data": {
            "user_id": current_admin.id,
            "username": current_admin.username,
            "role": current_admin.role,
        },
    }
