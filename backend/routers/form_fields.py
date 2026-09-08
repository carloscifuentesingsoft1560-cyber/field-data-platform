from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import FormField, FormVersion
from backend.schemas.form_field import(
    FormFieldCreate,
    FormFieldResponse
)

router = APIRouter(
    prefix="/form-fields",
    tags=["form-fields"]
)

@router.post(
    "/",
    response_model=FormFieldResponse,
    status_code=201
)
def create_form_field(
    field_data: FormFieldCreate,
    db: Session = Depends(get_db)
):
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field_data.form_version_id
        )
    )
    if not version:
        raise HTTPException(
            status_code=404,
            detail="Versión de formulario no encontrada"
        )

    if version.status != "draft":
        raise HTTPException(
            status_code= 400,
            detail="Solo se pueden modificar versiones en borrador"
        )
    existing_field = db.scalar(
        select(FormField).where(
            FormField.form_version_id == field_data.form_version_id,
            FormField.field_order == field_data.field_order
        )
    )

    if existing_field:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un campo con ese orden en esta versión"
        )

    new_field=FormField(
        form_version_id=field_data.form_version_id,
        name=field_data.name,
        field_type=field_data.field_type,
        field_order=field_data.field_order,
        is_required=field_data.is_required
    )

    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    return new_field


