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
from backend.schemas.user import (
    UserCreate,
    UserPasswordReset,
    UserResponse,
    UserUpdate,
)
from backend.security import (
    hash_password,
    require_control_role,
    require_password_reset_role,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[
        Depends(
            require_control_role
        )
    ],
)


# ============================================================
# CREAR USUARIO
# ============================================================

@router.post(
    "/",
    response_model=UserResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    responses={
        404: {
            "description":
                "Rol no encontrado"
        },
        409: {
            "description":
                "Usuario duplicado"
        },
    },
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(
        get_db
    ),
):
    employee_number = (
        user_data
        .employee_number
        .strip()
    )

    identification = (
        user_data
        .identification
        .strip()
    )

    existing_employee = db.scalar(
        select(User).where(
            User.employee_number
            == employee_number
        )
    )

    if existing_employee:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "El usuario ya está "
                "registrado"
            ),
        )

    existing_identification = (
        db.scalar(
            select(User).where(
                User.identification
                == identification
            )
        )
    )

    if existing_identification:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "La identificación "
                "ya está registrada"
            ),
        )

    existing_role = db.scalar(
        select(Role).where(
            Role.id
            == user_data.role_id
        )
    )

    if not existing_role:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "El rol especificado "
                "no existe"
            ),
        )

    db_user = User(
        employee_number=(
            employee_number
        ),

        identification=(
            identification
        ),

        password_hash=(
            hash_password(
                user_data.password
            )
        ),

        role_id=(
            user_data.role_id
        ),

        is_active=True,
    )

    db.add(
        db_user
    )

    db.commit()

    db.refresh(
        db_user
    )

    return db_user


# ============================================================
# LISTAR USUARIOS
# ============================================================

@router.get(
    "/",
    response_model=list[
        UserResponse
    ],
)
def list_users(
    db: Session = Depends(
        get_db
    ),
):
    users = db.scalars(
        select(User)
        .order_by(
            User.id
        )
    ).all()

    return users


# ============================================================
# CONSULTAR USUARIO
# ============================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        404: {
            "description":
                "Usuario no encontrado"
        }
    },
)
def get_user(
    user_id: int,
    db: Session = Depends(
        get_db
    ),
):
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Usuario no encontrado"
            ),
        )

    return user


# ============================================================
# ACTUALIZAR USUARIO
# ============================================================

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        400: {
            "description": (
                "Operación no permitida "
                "sobre el propio usuario"
            )
        },
        404: {
            "description":
                "Usuario o rol no encontrado"
        },
        409: {
            "description":
                "Datos de usuario duplicados"
        },
    },
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Usuario no encontrado"
            ),
        )

    update_data = (
        user_data.model_dump(
            exclude_unset=True
        )
    )

    # --------------------------------------------------------
    # PROTEGER EL PROPIO USUARIO
    # --------------------------------------------------------

    if (
        user_id
        == current_user.id
    ):
        if (
            "is_active"
            in update_data
            and update_data[
                "is_active"
            ] is False
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "No puede desactivar "
                    "su propio usuario"
                ),
            )

        if (
            "role_id"
            in update_data
            and update_data[
                "role_id"
            ]
            != current_user.role_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "No puede cambiar "
                    "su propio rol"
                ),
            )

    # --------------------------------------------------------
    # USUARIO / CÓDIGO DE ACCESO
    # --------------------------------------------------------

    if (
        "employee_number"
        in update_data
    ):
        employee_number = (
            update_data[
                "employee_number"
            ].strip()
        )

        if not employee_number:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "El usuario no puede "
                    "estar vacío"
                ),
            )

        existing_employee = (
            db.scalar(
                select(User).where(
                    User.employee_number
                    == employee_number,

                    User.id
                    != user_id,
                )
            )
        )

        if existing_employee:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El usuario ya está "
                    "registrado"
                ),
            )

        update_data[
            "employee_number"
        ] = employee_number

    # --------------------------------------------------------
    # IDENTIFICACIÓN
    # --------------------------------------------------------

    if (
        "identification"
        in update_data
    ):
        identification = (
            update_data[
                "identification"
            ].strip()
        )

        if not identification:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "La identificación no "
                    "puede estar vacía"
                ),
            )

        existing_identification = (
            db.scalar(
                select(User).where(
                    User.identification
                    == identification,

                    User.id
                    != user_id,
                )
            )
        )

        if existing_identification:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "La identificación "
                    "ya está registrada"
                ),
            )

        update_data[
            "identification"
        ] = identification

    # --------------------------------------------------------
    # ROL
    # --------------------------------------------------------

    if (
        "role_id"
        in update_data
    ):
        existing_role = db.scalar(
            select(Role).where(
                Role.id
                == update_data[
                    "role_id"
                ]
            )
        )

        if not existing_role:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "El rol especificado "
                    "no existe"
                ),
            )

    # --------------------------------------------------------
    # APLICAR CAMBIOS
    # --------------------------------------------------------

    for (
        field,
        value,
    ) in update_data.items():
        setattr(
            user,
            field,
            value,
        )

    db.commit()

    db.refresh(
        user
    )

    return user


# ============================================================
# RESTABLECER CONTRASEÑA
# SOLO DIRECTOR / JEFE NACIONAL
# ============================================================

@router.patch(
    "/{user_id}/reset-password",
    responses={
        200: {
            "description": (
                "Contraseña restablecida"
            )
        },
        400: {
            "description": (
                "No puede restablecer "
                "su propia contraseña "
                "desde esta función"
            )
        },
        403: {
            "description": (
                "Rol no autorizado"
            )
        },
        404: {
            "description": (
                "Usuario no encontrado"
            )
        },
    },
)
def reset_user_password(
    user_id: int,
    password_data:
        UserPasswordReset,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_password_reset_role
    ),
):
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Usuario no encontrado"
            ),
        )

    if (
        user.id
        == current_user.id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "No puede restablecer "
                "su propia contraseña "
                "desde esta función"
            ),
        )

    user.password_hash = (
        hash_password(
            password_data
            .new_password
        )
    )

    # Si estaba bloqueado por
    # intentos fallidos, el
    # restablecimiento lo desbloquea.
    user.failed_login_attempts = 0
    user.locked_until = None

    db.commit()

    return {
        "message": (
            "Contraseña restablecida "
            "correctamente"
        )
    }