from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Form, FormVersion
from backend.schemas.form_version import (
    FormVersionCreate,
    FormVersionResponse,
)

router = APIRouter(
    prefix="/form-versions",
    tags=["form-versions"]
)

@router.post(
    "/",
    response_model=FormVersionResponse,
    status_code=201
)

def create_form_version(
    version_data: FormVersionCreate,
    db: Session = Depends(get_db)
):
    form = db.scalar(
        select(Form).where(
            Form.id == version_data.form_id
        )
    )

    if not form:
        raise HTTPException(
            status_code=404,
            detail="Formulario no encontrado"
        )
    last_version = db.scalar(
        select(
            func.max(FormVersion.version_number)
        ).where(
            FormVersion.form_id == version_data.form_id
        )
    )
    next_version = (last_version or 0) + 1

    new_version = FormVersion(
        form_id = version_data.form_id,
        version_number = next_version,
        status ="draft"
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


@router.get(
    "/form/{form_id}",
    response_model=list[FormVersionResponse]
)

def get_form_versions(
    form_id: int,
    db: Session = Depends(get_db)
):
    versions = db.scalars(
        select(FormVersion).where(
            FormVersion.form_id == form_id
        ).order_by(
            FormVersion.version_number
        )
    ).all()

    return versions

@router.patch(
    "/{version_id}/publish",
    response_model=FormVersionResponse
)
def publish_form_version(
    version_id:int,
    db: Session = Depends(get_db)
):
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == version_id
        )
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail= "Versión de formulario no encontrada"
        )
    if version.status == "published":
        raise HTTPException(
            status_code=400,
            detail="La versión ya está publicada"
        )

    published_version = db.scalar(
        select(FormVersion).where(
            FormVersion.form_id == version.form_id,
            FormVersion.status == "published"
        )
    )

    if published_version:
        published_version.status ="archived"
    
    version.status = "published"


    db.commit()
    db.refresh(version)

    return version