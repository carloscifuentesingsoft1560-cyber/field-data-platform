from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Role
from backend.schemas.role import RoleResponse


router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)


# ============================================================
# LISTAR ROLES
# ============================================================

@router.get(
    "/",
    response_model=list[RoleResponse],
)
def get_roles(
    db: Session = Depends(get_db),
):
    roles = db.scalars(
        select(Role)
        .order_by(Role.id)
    ).all()

    return roles


# ============================================================
# CONSULTAR ROL POR ID
# ============================================================

@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        404: {
            "description": "Rol no encontrado"
        }
    },
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
):
    role = db.scalar(
        select(Role).where(
            Role.id == role_id
        )
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )

    return role