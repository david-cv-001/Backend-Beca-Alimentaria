from fastapi import APIRouter

from app.core.security import create_access_token
from app.db.session import SessionDep
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import AuthUser, LoginRequest, LoginResponse
from app.modules.auth.service import authenticate
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    name="AUTH_LOGIN",
    summary="Iniciar sesión",
)
async def login(payload: LoginRequest, session: SessionDep) -> ApiResponse[LoginResponse]:
    user = await authenticate(session, payload.username_or_email, payload.password)
    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        }
    )
    return ApiResponse(data=LoginResponse(access_token=token, user=AuthUser.from_user(user)))


@router.get(
    "/me",
    response_model=ApiResponse[AuthUser],
    name="AUTH_ME",
    summary="Usuario autenticado",
)
async def me(user: CurrentUser) -> ApiResponse[AuthUser]:
    return ApiResponse(data=AuthUser.from_user(user))
