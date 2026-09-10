from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import FormField, FormVersion
from backend.schemas.form_field import(
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldReorder,
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

@router.get(
    "/version/{form_version_id}",
    response_model=list[FormFieldResponse]
)
def get_form_fields_by_version(
    form_version_id: int,
    db: Session = Depends(get_db)
):
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Versión de formulario no encontrada"
        )

    fields = db.scalars(
        select(FormField).where(
            FormField.form_version_id == form_version_id
        ).order_by(
            FormField.field_order
        )
    ).all()

    return fields

@router.patch(
    "/{field_id}",
    response_model=FormFieldResponse
)
def update_form_field(
    field_id: int,
    field_data: FormFieldUpdate,
    db: Session = Depends(get_db)
):
    field = db.scalar(
        select(FormField).where(
            FormField.id == field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code= 404,
            detail="Campo de formulario no encontrado"
        )
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Versión de formulario no encontrada"
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden modificar campos de versiones en borrador"
        )

    update_data = field_data.model_dump(
        exclude_unset=True
    )

    if "field_order" in update_data:
        existing_field = db.scalar(
            select(FormField).where(
                FormField.form_version_id == field.form_version_id,
                FormField.field_order == update_data["field_order"],
                FormField.id != field.id
            )
        )

        if existing_field:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otro campo con ese orden en esta versión"
            )

    for field_name, value in update_data.items():
        setattr(field, field_name, value)

    db.commit()
    db.refresh(field)

    return field

@router.delete(
    "/{field_id}",
    status_code=204
)

def delete_form_field( 
    field_id:int,
    db:Session = Depends(get_db)
):
    field =  db.scalar(
        select(FormField).where(
            FormField.id == field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=404, 
            detail="Campo de formulario no encontrado"
        )

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Versión de formulario no encontrada"
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar campos de versiones en borrador"
        )

    delete_order = field.field_order
    form_version_id = field.form_version_id

    db.delete(field)
    db.flush()

    fields_to_shift = db.scalars(
        select(FormField).where(
            FormField.form_version_id == form_version_id,
            FormField.field_order > delete_order
        ).order_by(
            FormField.field_order
        )
    ).all()

    for other_field in fields_to_shift:
        other_field.field_order -= 1

    db.commit()

    return None

@router.patch(
    "/{field_id}/reorder",
    response_model=FormFieldResponse
)
def reorder_form_field(
    field_id: int,
    reorder_data: FormFieldReorder,
    db: Session = Depends(get_db)
):

    field = db.scalar(
        select(FormField).where(
            FormField.id == field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Campo de formulario no encontrado"
        )

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Versión de formulario no encontrada"
        )

    if version.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden reordenar campos de versiones en borrador"
        )

    fields = db.scalars(
        select(FormField).where(
            FormField.form_version_id == field.form_version_id
        ).order_by(
            FormField.field_order
        )
    ).all()

    total_fields = len(fields)

    if reorder_data.new_order < 1 or reorder_data.new_order > total_fields:
        raise HTTPException(
            status_code=400,
            detail=f"El nuevo orden debe estar entre 1 y {total_fields}"
        )
    
    if reorder_data.new_order == field.field_order:
        return field

    ordered_fields =[
        other_field
        for other_field in fields
        if other_field.id != field.id
    ]
    ordered_fields.insert(
        reorder_data.new_order - 1,
        field
    )

    temporary_offset = total_fields + 1 

    for other_field in fields:
        other_field.field_order += temporary_offset

    db.flush()    

    for position, other_field in enumerate(
        ordered_fields,
        start= 1
    ):
        other_field.field_order = position
        
    db.commit()
    db.refresh(field)

    return field
