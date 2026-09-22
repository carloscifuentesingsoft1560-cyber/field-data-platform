from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Role,
    User,
)
from backend.schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    TokenResponse,
)
from backend.security import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {
            "description": (
                "Credenciales incorrectas"
            )
        },
        403: {
            "description": (
                "Usuario inactivo"
            )
        },
    },
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(
        get_db
    ),
):
    user = db.scalar(
        select(User).where(
            User.employee_number
            == login_data.employee_number
        )
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Número de empleado "
                "o contraseña incorrectos"
            ),
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Número de empleado "
                "o contraseña incorrectos"
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "El usuario está inactivo"
            ),
        )

    access_token = (
        create_access_token(
            user.id
        )
    )

    return {
        "access_token": (
            access_token
        ),
        "token_type": "bearer",
        "expires_in": (
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            * 60
        ),
    }


# ============================================================
# USUARIO AUTENTICADO
# ============================================================

@router.get(
    "/me",
    response_model=AuthMeResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    role = db.scalar(
        select(Role).where(
            Role.id
            == current_user.role_id
        )
    )

    if role is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "El usuario tiene un rol inválido"
            ),
        )

    return {
        "id": current_user.id,
        "employee_number": (
            current_user.employee_number
        ),
        "identification": (
            current_user.identification
        ),
        "role_id": (
            current_user.role_id
        ),
        "role_name": (
            role.name
        ),
        "is_active": (
            current_user.is_active
        ),
    }