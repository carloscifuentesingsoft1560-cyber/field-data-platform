import os
from datetime import datetime, timedelta, timezone
from collections.abc import Callable

import jwt
from dotenv import load_dotenv
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Role, User


load_dotenv()


# ============================================================
# ROLES DEL SISTEMA
# ============================================================

CONTROL_ROLES = {
    "director",
    "jefe_nacional",
    "coordinador",
    "analista",
}

OPERATION_ROLES = {
    "auxiliar",
    "vendedor",
    "mercaimpulso",
}


# ============================================================
# CONTRASEÑAS
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(
    password: str,
) -> str:
    return password_hash.hash(
        password
    )


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


# ============================================================
# JWT
# ============================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY no está configurada en .env"
    )


JWT_ALGORITHM = "HS256"

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


def create_access_token(
    user_id: int,
) -> str:
    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return token


def decode_access_token(
    token: str,
) -> int:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        subject = payload.get(
            "sub"
        )

        if subject is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="Token inválido",
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        return int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Token inválido o expirado"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


# ============================================================
# USUARIO AUTENTICADO
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_current_user(
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(
        bearer_scheme
    ),
    db: Session = Depends(
        get_db
    ),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Se requiere autenticación"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user_id = decode_access_token(
        credentials.credentials
    )

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Usuario no encontrado",
            headers={
                "WWW-Authenticate": "Bearer"
            },
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

    return user


# ============================================================
# AUTORIZACIÓN POR ROL
# ============================================================

def require_roles(
    *allowed_roles: str,
) -> Callable:
    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
        db: Session = Depends(
            get_db
        ),
    ) -> User:
        role = db.scalar(
            select(Role).where(
                Role.id
                == current_user.role_id
            )
        )

        if role is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "El usuario no tiene "
                    "un rol válido"
                ),
            )

        if role.name not in allowed_roles:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "No tiene permisos para "
                    "realizar esta operación"
                ),
            )

        return current_user

    return role_checker


require_control_role = require_roles(
    *CONTROL_ROLES
)