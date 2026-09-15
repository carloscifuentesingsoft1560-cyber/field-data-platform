from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Survey,
    FormVersion,
    Form,
    User,
    UserProject,
)
from backend.schemas.survey import (
    SurveyCreate,
    SurveyResponse,
)


router = APIRouter(
    prefix="/surveys",
    tags=["surveys"],
)


@router.post(
    "/",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": SurveyResponse,
            "description": "La encuesta ya había sido procesada y se devuelve la existente",
        },
        400: {
            "description": "Versión no publicada, formulario inactivo o usuario inactivo",
        },
        403: {
            "description": "El usuario no está asignado al proyecto",
        },
        404: {
            "description": "Versión, formulario o usuario no encontrado",
        },
    },
    
)
def create_survey(
    survey_data: SurveyCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    # 1. Verificar si este UUID ya fue procesado
    existing_survey = db.scalar(
        select(Survey).where(
            Survey.uuid == survey_data.uuid
        )
    )

    if existing_survey is not None:
        response.status_code = status.HTTP_200_OK
        return existing_survey

    # 2. Verificar que la versión del formulario exista
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == survey_data.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada",
        )

    # 3. Solo se pueden diligenciar versiones publicadas
    if version.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden diligenciar versiones publicadas",
        )

    # 4. Buscar el formulario
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

    # Verificar que el formulario esté activo
    if not form.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formulario no está activo",
        )

    # 5. Verificar que el usuario exista
    user = db.scalar(
        select(User).where(
            User.id == survey_data.user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no está activo",
        )

    # 6. Verificar asignación usuario-proyecto
    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id == survey_data.user_id,
            UserProject.project_id == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este proyecto",
        )

    # 7. Crear la encuesta
    new_survey = Survey(
        uuid=survey_data.uuid,
        form_version_id=survey_data.form_version_id,
        user_id=survey_data.user_id,
        status="submitted",
        latitude=survey_data.latitude,
        longitude=survey_data.longitude,
        captured_at=survey_data.captured_at,
    )

    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)

    # MUY IMPORTANTE:
    # La función debe devolver el objeto creado.
    return new_survey

@router.get(
    "/",
    response_model=list[SurveyResponse],
)
def get_surveys(
    db: Session = Depends(get_db),
):
    surveys = db.scalars(
        select(Survey).order_by(
            Survey.received_at.desc()
        )
    ).all()

    return surveys


@router.get(
    "/by-uuid/{survey_uuid}",
    response_model=SurveyResponse,
    responses={
        404: {
            "description": "Encuesta no encontrada"
        }
    },
)
def get_survey_by_uuid(
    survey_uuid: UUID,
    db: Session = Depends(get_db),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.uuid == survey_uuid
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    return survey


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    responses={
        404: {
            "description": "Encuesta no encontrada"
        }
    },
)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.id == survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    return survey