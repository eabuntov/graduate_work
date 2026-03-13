from fastapi import APIRouter, Depends

from dependencies import get_user_service
from models.models import UserRead, PasswordChange, StandardResponse
from security.auth import get_current_user
from services.user_service import UserService
from rate_limit.rate_limiter import rate_limit

users_router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(rate_limit("auth"))])


@users_router.get("/me", response_model=UserRead)
async def get_me(current=Depends(get_current_user)):
    return current


@users_router.post("/change-password", response_model=StandardResponse)
async def change_password(
    data: PasswordChange,
    current=Depends(get_current_user),
    users: UserService = Depends(get_user_service),
):
    await users.change_password(current, data.old_password, data.new_password)
    return {"detail": "Password updated"}
