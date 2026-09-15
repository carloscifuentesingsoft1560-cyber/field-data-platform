from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Survey,
    SurveyAnswer,
    FormField,
    FieldOption,
)
from backend.schemas.survey_answer import (
    SurveyAnswerCreate,
    SurveyAnswerResponse,
)


router = APIRouter(
    prefix="/survey-answers",
    tags=["survey-answers"],
)


@router.post(
    "/",
    response_model=SurveyAnswerResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "Respuesta incompatible con el tipo de campo"
        },
        404: {
            "description": "Encuesta o campo no encontrado"
        },
        409: {
            "description": "El campo ya fue respondido en esta encuesta"
        },
    },
)
def create_survey_answer(
    answer_data: SurveyAnswerCreate,
    db: Session = Depends(get_db),
):
    # 1. Verificar que la encuesta exista
    survey = db.scalar(
        select(Survey).where(
            Survey.id == answer_data.survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    # 2. Verificar que el campo exista
    field = db.scalar(
        select(FormField).where(
            FormField.id == answer_data.form_field_id
        )
    )

    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo de formulario no encontrado",
        )

    # 3. El campo debe pertenecer a la misma versión de la encuesta
    if field.form_version_id != survey.form_version_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo no pertenece a la versión del formulario de esta encuesta",
        )

    # 4. No permitir dos respuestas para la misma pregunta
    existing_answer = db.scalar(
        select(SurveyAnswer).where(
            SurveyAnswer.survey_id == answer_data.survey_id,
            SurveyAnswer.form_field_id == answer_data.form_field_id,
        )
    )

    if existing_answer is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este campo ya fue respondido en esta encuesta",
        )

    # 5. Validar el valor según el tipo de campo
    if field.field_type in ("text", "textarea"):
        if answer_data.value_text is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este campo requiere value_text",
            )

        if (
            answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un campo de texto solo puede utilizar value_text",
            )

    elif field.field_type == "number":
        if answer_data.value_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este campo requiere value_number",
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un campo numérico solo puede utilizar value_number",
            )

    elif field.field_type == "date":
        if answer_data.value_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este campo requiere value_date",
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un campo de fecha solo puede utilizar value_date",
            )

    elif field.field_type == "boolean":
        if answer_data.value_boolean is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este campo requiere value_boolean",
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un campo booleano solo puede utilizar value_boolean",
            )

    elif field.field_type == "select":
        if answer_data.field_option_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este campo requiere field_option_id",
            )

        option = db.scalar(
            select(FieldOption).where(
                FieldOption.id == answer_data.field_option_id,
                FieldOption.form_field_id == field.id,
            )
        )

        if option is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La opción seleccionada no pertenece a este campo",
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un campo select solo puede utilizar field_option_id",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de campo no soportado",
        )

    # 6. Crear la respuesta
    new_answer = SurveyAnswer(
        survey_id=answer_data.survey_id,
        form_field_id=answer_data.form_field_id,
        value_text=answer_data.value_text,
        value_number=answer_data.value_number,
        value_date=answer_data.value_date,
        value_boolean=answer_data.value_boolean,
        field_option_id=answer_data.field_option_id,
    )

    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)

    return new_answer


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
