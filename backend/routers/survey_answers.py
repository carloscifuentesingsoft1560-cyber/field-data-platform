from datetime import date
from decimal import Decimal
from typing import TypedDict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldOption,
    Form,
    FormField,
    FormVersion,
    Survey,
    SurveyAnswer,
    SurveyAnswerCorrection,
    User,
    UserProject,
)
from backend.schemas.survey_answer import (
    SurveyAnswerCorrectionResponse,
    SurveyAnswerCorrectionResult,
    SurveyAnswerResponse,
    SurveyAnswerUpdate,
)


router = APIRouter(
    prefix="/survey-answers",
    tags=["survey-answers"],
)


# ============================================================
# TIPO INTERNO PARA VALORES DE RESPUESTA
# ============================================================

class AnswerValues(TypedDict):
    value_text: str | None
    value_number: Decimal | None
    value_date: date | None
    value_boolean: bool | None
    field_option_id: int | None


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_correction_value(
    field: FormField,
    answer_data: SurveyAnswerUpdate,
    db: Session,
) -> AnswerValues:
    """
    Valida que el nuevo valor corresponda exactamente
    al tipo configurado para el FormField.

    Devuelve todos los valores normalizados para poder
    actualizar SurveyAnswer de forma segura.
    """

    values: AnswerValues = {
        "value_text": None,
        "value_number": None,
        "value_date": None,
        "value_boolean": None,
        "field_option_id": None,
    }

    # --------------------------------------------------------
    # TEXT / TEXTAREA
    # --------------------------------------------------------

    if field.field_type in (
        "text",
        "textarea",
    ):
        if answer_data.value_text is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "requiere value_text"
                ),
            )

        if (
            answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "solo admite value_text"
                ),
            )

        values["value_text"] = (
            answer_data.value_text
        )

    # --------------------------------------------------------
    # NUMBER
    # --------------------------------------------------------

    elif field.field_type == "number":
        if answer_data.value_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "requiere value_number"
                ),
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "solo admite value_number"
                ),
            )

        values["value_number"] = (
            answer_data.value_number
        )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    elif field.field_type == "date":
        if answer_data.value_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "requiere value_date"
                ),
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_boolean is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "solo admite value_date"
                ),
            )

        values["value_date"] = (
            answer_data.value_date
        )

    # --------------------------------------------------------
    # BOOLEAN
    # --------------------------------------------------------

    elif field.field_type == "boolean":
        if answer_data.value_boolean is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "requiere value_boolean"
                ),
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.field_option_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "solo admite value_boolean"
                ),
            )

        values["value_boolean"] = (
            answer_data.value_boolean
        )

    # --------------------------------------------------------
    # SELECT
    # --------------------------------------------------------

    elif field.field_type == "select":
        if answer_data.field_option_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "requiere field_option_id"
                ),
            )

        option = db.scalar(
            select(FieldOption).where(
                FieldOption.id
                == answer_data.field_option_id,
                FieldOption.form_field_id
                == field.id,
            )
        )

        if option is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La opción seleccionada no pertenece "
                    f"al campo {field.id}"
                ),
            )

        if (
            answer_data.value_text is not None
            or answer_data.value_number is not None
            or answer_data.value_date is not None
            or answer_data.value_boolean is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {field.id} "
                    "solo admite field_option_id"
                ),
            )

        values["field_option_id"] = (
            answer_data.field_option_id
        )

    # --------------------------------------------------------
    # TIPO NO SOPORTADO
    # --------------------------------------------------------

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tipo de campo no soportado: "
                f"{field.field_type}"
            ),
        )

    return values