from fastapi import APIRouter

from api.v1.auth_router import auth_router
from api.v1.roles_router import roles_router
from api.v1.subscriptions_router import subscriptions_router
from api.v1.users_router import users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(subscriptions_router)
