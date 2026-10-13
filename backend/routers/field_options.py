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
    FieldOption,
    Form,
    FormField,
    FormVersion,
    User,
    UserProject,
)
from backend.schemas.field_option import (
    FieldOptionCreate,
    FieldOptionResponse,
    FieldOptionUpdate,
)
from backend.security import (
    get_current_user,
    require_control_role,
)


router = APIRouter(
    prefix="/field-options",
    tags=["field-options"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_field_access(
    form_field_id: int,
    current_user: User,
    db: Session,
) -> tuple[
    FormField,
    FormVersion,
]:
    """
    Valida que el campo exista y que el usuario
    esté asignado al proyecto al que pertenece
    el formulario de la versión del campo.
    """

    field = db.scalar(
        select(FormField).where(
            FormField.id == form_field_id
        )
    )

    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Campo de formulario "
                "no encontrado"
            ),
        )

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == field.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    form = db.scalar(
        select(Form).where(
            Form.id == version.form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
        )

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id
            == current_user.id,
            UserProject.project_id
            == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    return (
        field,
        version,
    )


def validate_option_access(
    option_id: int,
    current_user: User,
    db: Session,
) -> tuple[
    FieldOption,
    FormField,
    FormVersion,
]:
    """
    Valida que la opción exista y que el usuario
    tenga acceso al proyecto del campo al que
    pertenece.
    """

    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id == option_id
        )
    )

    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Opción de campo "
                "no encontrada"
            ),
        )

    (
        field,
        version,
    ) = validate_field_access(
        form_field_id=option.form_field_id,
        current_user=current_user,
        db=db,
    )

    return (
        option,
        field,
        version,
    )


# ============================================================
# CREAR OPCIÓN
# ============================================================

@router.post(
    "/",
    response_model=FieldOptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": (
                "Versión no editable, campo "
                "inválido o dato duplicado"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Rol no autorizado o usuario "
                "sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Campo, versión o formulario "
                "no encontrado"
            )
        },
    },
)
def create_field_option(
    option_data: FieldOptionCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    (
        field,
        version,
    ) = validate_field_access(
        form_field_id=(
            option_data.form_field_id
        ),
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden modificar "
                "opciones de versiones "
                "en borrador"
            ),
        )

    if field.field_type != "select":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo los campos de tipo "
                "select pueden tener opciones"
            ),
        )

    existing_order = db.scalar(
        select(FieldOption).where(
            FieldOption.form_field_id
            == option_data.form_field_id,
            FieldOption.option_order
            == option_data.option_order,
        )
    )

    if existing_order is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Ya existe una opción con "
                "ese orden en este campo"
            ),
        )

    existing_value = db.scalar(
        select(FieldOption).where(
            FieldOption.form_field_id
            == option_data.form_field_id,
            FieldOption.value
            == option_data.value,
        )
    )

    if existing_value is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Ya existe una opción con "
                "ese valor en este campo"
            ),
        )

    new_option = FieldOption(
        form_field_id=(
            option_data.form_field_id
        ),
        label=option_data.label,
        value=option_data.value,
        option_order=(
            option_data.option_order
        ),
    )

    db.add(
        new_option
    )

    db.commit()

    db.refresh(
        new_option
    )

    return new_option


# ============================================================
# CONSULTAR OPCIONES DE UN CAMPO
# ============================================================

@router.get(
    "/by-field/{form_field_id}",
    response_model=list[
        FieldOptionResponse
    ],
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Campo, versión o formulario "
                "no encontrado"
            )
        },
    },
)
def get_field_option_by_field(
    form_field_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    validate_field_access(
        form_field_id=form_field_id,
        current_user=current_user,
        db=db,
    )

    options = db.scalars(
        select(FieldOption)
        .where(
            FieldOption.form_field_id
            == form_field_id
        )
        .order_by(
            FieldOption.option_order
        )
    ).all()

    return options


# ============================================================
# CONSULTAR UNA OPCIÓN
# ============================================================

@router.get(
    "/{option_id}",
    response_model=FieldOptionResponse,
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Opción, campo, versión "
                "o formulario no encontrado"
            )
        },
    },
)
def get_field_option(
    option_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    (
        option,
        _,
        _,
    ) = validate_option_access(
        option_id=option_id,
        current_user=current_user,
        db=db,
    )

    return option


# ============================================================
# ACTUALIZAR OPCIÓN
# ============================================================

@router.patch(
    "/{option_id}",
    response_model=FieldOptionResponse,
    responses={
        400: {
            "description": (
                "Versión no editable o "
                "dato duplicado"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Rol no autorizado o usuario "
                "sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Opción, campo, versión "
                "o formulario no encontrado"
            )
        },
    },
)
def update_field_option(
    option_id: int,
    option_data: FieldOptionUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    (
        option,
        _,
        version,
    ) = validate_option_access(
        option_id=option_id,
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden modificar "
                "opciones de versiones "
                "en borrador"
            ),
        )

    if (
        option_data.option_order
        is not None
        and option_data.option_order
        != option.option_order
    ):
        existing_order = db.scalar(
            select(FieldOption).where(
                FieldOption.form_field_id
                == option.form_field_id,
                FieldOption.option_order
                == option_data.option_order,
                FieldOption.id
                != option_id,
            )
        )

        if existing_order is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Ya existe una opción "
                    "con ese orden en "
                    "este campo"
                ),
            )

    if (
        option_data.value is not None
        and option_data.value
        != option.value
    ):
        existing_value = db.scalar(
            select(FieldOption).where(
                FieldOption.form_field_id
                == option.form_field_id,
                FieldOption.value
                == option_data.value,
                FieldOption.id
                != option_id,
            )
        )

        if existing_value is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Ya existe una opción "
                    "con ese valor en "
                    "este campo"
                ),
            )

    update_data = (
        option_data.model_dump(
            exclude_unset=True
        )
    )

    for field_name, value in (
        update_data.items()
    ):
        setattr(
            option,
            field_name,
            value,
        )

    db.commit()

    db.refresh(
        option
    )

    return option


# ============================================================
# ELIMINAR OPCIÓN
# ============================================================

@router.delete(
    "/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {
            "description": (
                "La versión no está "
                "en borrador"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Rol no autorizado o usuario "
                "sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Opción, campo, versión "
                "o formulario no encontrado"
            )
        },
    },
)
def delete_field_option(
    option_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    (
        option,
        _,
        version,
    ) = validate_option_access(
        option_id=option_id,
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden eliminar "
                "opciones de versiones "
                "en borrador"
            ),
        )

    db.delete(
        option
    )

    db.commit()

    return None