from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import FieldOption, FormField, FormVersion
from backend.schemas.field_option import (
    FieldOptionCreate,
    FieldOptionUpdate,
    FieldOptionResponse,
)

router = APIRouter(
    prefix="/field-options",
    tags=["field-options"],
)


@router.post(
    "/",
    response_model=FieldOptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_field_option(
    option_data: FieldOptionCreate,
    db: Session = Depends(get_db),
):
    # 1. Verificar que el campo exista
    field = db.scalar(
        select(FormField).where(
            FormField.id == option_data.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo de formulario no encontrado",
        )

    # 2. Obtener la versión a la que pertenece el campo
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada",
        )

    # 3. Solo permitir cambios en versiones draft
    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden modificar opciones de versiones en borrador",
        )

    # 4. Solo campos select pueden tener opciones
    if field.field_type != "select":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo los campos de tipo select pueden tener opciones",
        )

    # 5. Evitar option_order duplicado dentro del mismo campo
    existing_order = db.scalar(
        select(FieldOption).where(
            FieldOption.form_field_id == option_data.form_field_id,
            FieldOption.option_order == option_data.option_order,
        )
    )

    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una opción con ese orden en este campo",
        )

    # 6. Evitar value duplicado dentro del mismo campo
    existing_value = db.scalar(
        select(FieldOption).where(
            FieldOption.form_field_id == option_data.form_field_id,
            FieldOption.value == option_data.value,
        )
    )

    if existing_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una opción con ese valor en este campo",
        )

    # 7. Crear opción
    new_option = FieldOption(
        form_field_id=option_data.form_field_id,
        label=option_data.label,
        value=option_data.value,
        option_order=option_data.option_order,
    )

    db.add(new_option)
    db.commit()
    db.refresh(new_option)

    return new_option

@router.get(
    "/by-field/{form_field_id}",
    response_model= list[FieldOptionResponse]
)
def get_field_option_by_field(
    form_field_id:int,
    db: Session = Depends(get_db)
):

    field = db.scalar(
        select(FormField).where(
            FormField.id == form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Campo de formulario no encontrado"
        )

    options = db.scalars(
        select(FieldOption).where(
            FieldOption.form_field_id == form_field_id
        ).order_by(FieldOption.option_order)
    ).all()

    return options

@router.get(
    "/{option_id}",
    response_model= FieldOptionResponse
)
def get_field_option(
    option_id: int,
    db:Session = Depends(get_db)
):
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=404,
            detail="Opción de campo no encontrada"
        )

    return option

@router.patch(
    "/{option_id}",
    response_model=FieldOptionResponse
)
def update_field_option(
    option_id: int,
    option_data: FieldOptionUpdate,
    db: Session = Depends(get_db)
):
   
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opción de campo no encontrada"
        )

    
    field = db.scalar(
        select(FormField).where(
            FormField.id == option.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo de formulario no encontrado"
        )

   
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada"
        )

   
    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden modificar opciones de versiones en borrador"
        )

  
    if (
        option_data.option_order is not None
        and option_data.option_order != option.option_order
    ):
        existing_order = db.scalar(
            select(FieldOption).where(
                FieldOption.form_field_id == option.form_field_id,
                FieldOption.option_order == option_data.option_order,
                FieldOption.id != option_id
            )
        )

        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una opción con ese orden en este campo"
            )

   
    if (
        option_data.value is not None
        and option_data.value != option.value
    ):
        existing_value = db.scalar(
            select(FieldOption).where(
                FieldOption.form_field_id == option.form_field_id,
                FieldOption.value == option_data.value,
                FieldOption.id != option_id
            )
        )

        if existing_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una opción con ese valor en este campo"
            )

   
    update_data = option_data.model_dump(
        exclude_unset=True
    )

    for field_name, value in update_data.items():
        setattr(option, field_name, value)

    db.commit()
    db.refresh(option)

    return option

@router.delete(
    "/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_field_option(
    option_id: int,
    db: Session = Depends(get_db)
):
    # 1. Buscar la opción
    option = db.scalar(
        select(FieldOption).where(
            FieldOption.id == option_id
        )
    )

    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opción de campo no encontrada"
        )

    # 2. Buscar el campo al que pertenece
    field = db.scalar(
        select(FormField).where(
            FormField.id == option.form_field_id
        )
    )

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo de formulario no encontrado"
        )

    # 3. Buscar la versión del formulario
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == field.form_version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada"
        )

    # 4. Solo borrar opciones de versiones draft
    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden eliminar opciones de versiones en borrador"
        )

    # 5. Eliminar
    db.delete(option)
    db.commit()