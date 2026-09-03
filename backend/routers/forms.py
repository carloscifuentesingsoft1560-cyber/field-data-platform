from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Form, Project
from backend.schemas.form import (
    FormCreate,
    FormResponse,
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