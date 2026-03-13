from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_role_service
from models.models import (
    RoleRead,
    RoleCreate,
    StandardResponse,
    UserRoleInput,
    RoleType,
)
from security.auth import require_permissions, role_types_required
from services.role_service import RoleService
from rate_limit.rate_limiter import rate_limit

roles_router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(rate_limit("auth"))])


@roles_router.post(
    "/",
    response_model=RoleRead,
    dependencies=[Depends(require_permissions(["manage_roles"]))],
)
@role_types_required(allowed_types=[RoleType.ADMIN])
async def create_role(data: RoleCreate, roles: RoleService = Depends(get_role_service)):
    return await roles.create_role(data.name, data.permissions, data.description)


@roles_router.get("/", response_model=list[RoleRead])
async def list_roles(roles: RoleService = Depends(get_role_service)):
    return await roles.list_roles()


@roles_router.patch("/{role_id}/assign/{user_id}", response_model=None)
@role_types_required(allowed_types=[RoleType.ADMIN])
async def assign_role(
    user_role: UserRoleInput, roles: RoleService = Depends(get_role_service)
):
    try:
        await roles.assign_role(user_id=user_role.user_id, role_id=user_role.role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "Role assigned"}


@roles_router.delete("/{role_id}/remove/{user_id}", response_model=StandardResponse)
@role_types_required(allowed_types=[RoleType.ADMIN])
async def remove_role(
    user_role: UserRoleInput, roles: RoleService = Depends(get_role_service)
):
    try:
        await roles.remove_role(user_id=user_role.user_id, role_id=user_role.role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "Role removed"}
