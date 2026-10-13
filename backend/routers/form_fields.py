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
    Form,
    FormField,
    FormVersion,
    User,
    UserProject,
)
from backend.schemas.form_field import (
    FormFieldCreate,
    FormFieldReorder,
    FormFieldResponse,
    FormFieldUpdate,
)
from backend.security import (
    get_current_user,
    require_control_role,
)


router = APIRouter(
    prefix="/form-fields",
    tags=["form-fields"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_version_access(
    form_version_id: int,
    current_user: User,
    db: Session,
) -> FormVersion:
    """
    Valida que la versión exista y que el usuario
    esté asignado al proyecto al que pertenece
    el formulario de la versión.
    """

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == form_version_id
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

    return version


def validate_field_access(
    field_id: int,
    current_user: User,
    db: Session,
) -> tuple[
    FormField,
    FormVersion,
]:
    """
    Valida que el campo exista y que el usuario
    tenga acceso al proyecto de la versión
    a la que pertenece.
    """

    field = db.scalar(
        select(FormField).where(
            FormField.id == field_id
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

    version = validate_version_access(
        form_version_id=field.form_version_id,
        current_user=current_user,
        db=db,
    )

    return (
        field,
        version,
    )


# ============================================================
# CREAR CAMPO
# ============================================================

@router.post(
    "/",
    response_model=FormFieldResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": (
                "Versión no editable o "
                "orden duplicado"
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
                "Versión de formulario "
                "no encontrada"
            )
        },
    },
)
def create_form_field(
    field_data: FormFieldCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    version = validate_version_access(
        form_version_id=(
            field_data.form_version_id
        ),
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden modificar "
                "versiones en borrador"
            ),
        )

    existing_field = db.scalar(
        select(FormField).where(
            FormField.form_version_id
            == field_data.form_version_id,
            FormField.field_order
            == field_data.field_order,
        )
    )

    if existing_field is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Ya existe un campo con "
                "ese orden en esta versión"
            ),
        )

    new_field = FormField(
        form_version_id=(
            field_data.form_version_id
        ),
        name=field_data.name,
        field_type=field_data.field_type,
        field_order=field_data.field_order,
        is_required=field_data.is_required,
    )

    db.add(
        new_field
    )

    db.commit()

    db.refresh(
        new_field
    )

    return new_field


# ============================================================
# CONSULTAR CAMPOS DE UNA VERSIÓN
# ============================================================

@router.get(
    "/version/{form_version_id}",
    response_model=list[
        FormFieldResponse
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
                "Versión de formulario "
                "no encontrada"
            )
        },
    },
)
def get_form_fields_by_version(
    form_version_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    validate_version_access(
        form_version_id=form_version_id,
        current_user=current_user,
        db=db,
    )

    fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == form_version_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    return fields


# ============================================================
# ACTUALIZAR CAMPO
# ============================================================

@router.patch(
    "/{field_id}",
    response_model=FormFieldResponse,
    responses={
        400: {
            "description": (
                "Versión no editable o "
                "orden duplicado"
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
                "Campo o versión "
                "no encontrada"
            )
        },
    },
)
def update_form_field(
    field_id: int,
    field_data: FormFieldUpdate,
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
        field_id=field_id,
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden modificar "
                "campos de versiones "
                "en borrador"
            ),
        )

    update_data = (
        field_data.model_dump(
            exclude_unset=True
        )
    )

    if "field_order" in update_data:
        existing_field = db.scalar(
            select(FormField).where(
                FormField.form_version_id
                == field.form_version_id,
                FormField.field_order
                == update_data[
                    "field_order"
                ],
                FormField.id != field.id,
            )
        )

        if existing_field is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Ya existe otro campo "
                    "con ese orden en esta "
                    "versión"
                ),
            )

    for field_name, value in (
        update_data.items()
    ):
        setattr(
            field,
            field_name,
            value,
        )

    db.commit()

    db.refresh(
        field
    )

    return field


# ============================================================
# ELIMINAR CAMPO
# ============================================================

@router.delete(
    "/{field_id}",
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
                "Campo o versión "
                "no encontrada"
            )
        },
    },
)
def delete_form_field(
    field_id: int,
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
        field_id=field_id,
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden eliminar "
                "campos de versiones "
                "en borrador"
            ),
        )

    delete_order = (
        field.field_order
    )

    form_version_id = (
        field.form_version_id
    )

    db.delete(
        field
    )

    db.flush()

    fields_to_shift = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == form_version_id,
            FormField.field_order
            > delete_order,
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    for other_field in (
        fields_to_shift
    ):
        other_field.field_order -= 1

    db.commit()

    return None


# ============================================================
# REORDENAR CAMPO
# ============================================================

@router.patch(
    "/{field_id}/reorder",
    response_model=FormFieldResponse,
    responses={
        400: {
            "description": (
                "Versión no editable o "
                "orden inválido"
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
                "Campo o versión "
                "no encontrada"
            )
        },
    },
)
def reorder_form_field(
    field_id: int,
    reorder_data: FormFieldReorder,
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
        field_id=field_id,
        current_user=current_user,
        db=db,
    )

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden reordenar "
                "campos de versiones "
                "en borrador"
            ),
        )

    fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == field.form_version_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    total_fields = len(
        fields
    )

    if (
        reorder_data.new_order < 1
        or reorder_data.new_order
        > total_fields
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El nuevo orden debe estar "
                f"entre 1 y {total_fields}"
            ),
        )

    if (
        reorder_data.new_order
        == field.field_order
    ):
        return field

    ordered_fields = [
        other_field
        for other_field in fields
        if other_field.id != field.id
    ]

    ordered_fields.insert(
        reorder_data.new_order - 1,
        field,
    )

    temporary_offset = (
        total_fields + 1
    )

    for other_field in fields:
        other_field.field_order += (
            temporary_offset
        )

    db.flush()

    for position, other_field in (
        enumerate(
            ordered_fields,
            start=1,
        )
    ):
        other_field.field_order = (
            position
        )

    db.commit()

    db.refresh(
        field
    )

    return field