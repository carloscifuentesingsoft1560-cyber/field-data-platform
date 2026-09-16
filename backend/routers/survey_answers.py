from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Survey,
    SurveyAnswer,
    FormField,
)
from backend.schemas.survey_answer import SurveyAnswerResponse


router = APIRouter(
    prefix="/survey-answers",
    tags=["survey-answers"],
)

@router.get(
    "/by-survey/{survey_id}",
    response_model=list[SurveyAnswerResponse],
    responses={
        404: {
            "description": "Encuesta no encontrada"
        }
    },
)
def get_answers_by_survey(
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

    answers = db.scalars(
        select(SurveyAnswer)
        .join(
            FormField,
            SurveyAnswer.form_field_id == FormField.id
        )
        .where(
            SurveyAnswer.survey_id == survey_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    return answers


@router.get(
    "/{answer_id}",
    response_model=SurveyAnswerResponse,
    responses={
        404: {
            "description": "Respuesta no encontrada"
        }
    },
)
def get_survey_answer(
    answer_id: int,
    db: Session = Depends(get_db),
):
    answer = db.scalar(
        select(SurveyAnswer).where(
            SurveyAnswer.id == answer_id
        )
    )

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Respuesta no encontrada",
        )

    return answer
