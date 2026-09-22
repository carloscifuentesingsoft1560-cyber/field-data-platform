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
    FormField,
    FormVersion,
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
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.post(
    "/",
    response_model=FieldOptionResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    dependencies=[
        Depends(require_control_role)
    ],
)
def create_field_option(
    option_data: FieldOptionCreate,
    db: Session = Depends(get_db),
):
    field = db.scalar(
        select(FormField).where(
            FormField.id
            == option_data.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
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

    if not version:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Solo se pueden modificar "
                "opciones de versiones "
                "en borrador"
            ),
        )

    if field.field_type != "select":
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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

    if existing_order:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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

    if existing_value:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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

    db.add(new_option)
    db.commit()
    db.refresh(new_option)

    return new_option


@router.get(
    "/by-field/{form_field_id}",
    response_model=list[
        FieldOptionResponse
    ],
)
def get_field_option_by_field(
    form_field_id: int,
    db: Session = Depends(get_db),
):
    field = db.scalar(
        select(FormField).where(
            FormField.id
            == form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=404,
            detail=(
                "Campo de formulario "
                "no encontrado"
            ),
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


@router.get(
    "/{option_id}",
    response_model=FieldOptionResponse,
)
def get_field_option(
    option_id: int,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id
            == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=404,
            detail=(
                "Opción de campo "
                "no encontrada"
            ),
        )

    return option


@router.patch(
    "/{option_id}",
    response_model=FieldOptionResponse,
    dependencies=[
        Depends(require_control_role)
    ],
)
def update_field_option(
    option_id: int,
    option_data: FieldOptionUpdate,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id
            == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Opción de campo "
                "no encontrada"
            ),
        )

    field = db.scalar(
        select(FormField).where(
            FormField.id
            == option.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
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

    if not version:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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

        if existing_order:
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

        if existing_value:
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
    db.refresh(option)

    return option


@router.delete(
    "/{option_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
    dependencies=[
        Depends(require_control_role)
    ],
)
def delete_field_option(
    option_id: int,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id
            == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Opción de campo "
                "no encontrada"
            ),
        )

    field = db.scalar(
        select(FormField).where(
            FormField.id
            == option.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
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

    if not version:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Solo se pueden eliminar "
                "opciones de versiones "
                "en borrador"
            ),
        )

    db.delete(option)
    db.commit()

    return None