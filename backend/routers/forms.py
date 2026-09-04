from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Form, Project
from backend.schemas.form import (
    FormCreate,
    FormResponse,
    FormUpdate,
    )

router = APIRouter(
    prefix="/forms",
    tags=["forms"]
)

@router.post(
    "/",
    response_model = FormResponse,
    status_code = 201,
    responses={
        404:{"description": "Proyecto no encontrado"}
    }
)
def create_form(
    form:FormCreate,
    db: Session = Depends(get_db)
): 
    project = db.scalar(
        select(Project).where(
            Project.id == form.project_id
        )
    )
    if not project:
        raise HTTPException(
            status_code= 404,
            detail= "Proyecto no encontrado"
        )
    db_form =Form(
        project_id = form.project_id,
        name = form.name,
        description = form.description
    )

    db.add(db_form)
    db.commit()
    db.refresh(db_form)

    return db_form
@router.get(
    "/",
    response_model = list[FormResponse]
)

def get_forms(
    db: Session = Depends(get_db)
): 
    forms = db.scalars(
        select(Form)
    ).all()

    return forms

@router.get(
    "/{form_id}",
    response_model = FormResponse
)

def get_form(
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.scalar(
        select(Form).where(
            Form.id == form_id
        )
    )

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Formulario  no encontrado"
        )

    return form

@router.patch(
    "/{form_id}",
    response_model = FormResponse 
)
def update_form(
    form_id: int,
    form_data: FormUpdate,
    db: Session = Depends(get_db)
):
    form = db.scalar(
        select(Form).where(
            Form.id == form_id
        )
    )

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Formulario no encontrado"
        )

    update_data = form_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(form, field, value)

    db.commit()
    db.refresh(form)

    return form