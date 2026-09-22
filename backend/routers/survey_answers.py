from datetime import date
from decimal import Decimal
from typing import TypedDict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
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
    SurveyAnswerCorrectionResponse
    as SurveyAnswerCorrectionResponseSchema,
    SurveyAnswerCorrectionResult
    as SurveyAnswerCorrectionResultSchema,
    SurveyAnswerResponse
    as SurveyAnswerResponseSchema,
    SurveyAnswerUpdate
    as SurveyAnswerUpdateSchema,
)
from backend.security import (
    get_current_user,
    require_control_role,
)


router = APIRouter(
    prefix="/survey-answers",
    tags=["survey-answers"],
    dependencies=[
        Depends(get_current_user)
    ],
)


# ============================================================
# TIPOS INTERNOS
# ============================================================

class AnswerValues(TypedDict):
    value_text: str | None
    value_number: Decimal | None
    value_date: date | None
    value_boolean: bool | None
    field_option_id: int | None


# ============================================================
# VALIDACIÓN DEL NUEVO VALOR
# ============================================================

def validate_correction_value(
    field: FormField,
    answer_data: SurveyAnswerUpdateSchema,
    db: Session,
) -> AnswerValues:
    """
    Valida que el nuevo valor corresponda exactamente
    al tipo configurado para el FormField.
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
                    "La opción seleccionada "
                    "no pertenece al campo "
                    f"{field.id}"
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


# ============================================================
# CONSULTAR RESPUESTAS DE UNA ENCUESTA
# ============================================================

@router.get(
    "/by-survey/{survey_id}",
    response_model=list[
        SurveyAnswerResponseSchema
    ],
    responses={
        404: {
            "description": (
                "Encuesta no encontrada"
            )
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
            SurveyAnswer.form_field_id
            == FormField.id,
        )
        .where(
            SurveyAnswer.survey_id
            == survey_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    return answers


# ============================================================
# CONSULTAR UNA RESPUESTA
# ============================================================

@router.get(
    "/{answer_id}",
    response_model=SurveyAnswerResponseSchema,
    responses={
        404: {
            "description": (
                "Respuesta no encontrada"
            )
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


# ============================================================
# CORREGIR UNA RESPUESTA
# ============================================================

@router.patch(
    "/{answer_id}",
    response_model=(
        SurveyAnswerCorrectionResultSchema
    ),
    responses={
        400: {
            "description": (
                "Corrección inválida"
            )
        },
        403: {
            "description": (
                "Rol no autorizado o usuario "
                "sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Respuesta, campo, encuesta "
                "o formulario no encontrado"
            )
        },
    },
)
def correct_survey_answer(
    answer_id: int,
    answer_data: SurveyAnswerUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_control_role
    ),
):
    # --------------------------------------------------------
    # 1. RESPUESTA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 2. CAMPO
    # --------------------------------------------------------

    field = db.scalar(
        select(FormField).where(
            FormField.id
            == answer.form_field_id
        )
    )

    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Campo de formulario no encontrado"
            ),
        )

    # --------------------------------------------------------
    # 3. ENCUESTA
    # --------------------------------------------------------

    survey = db.scalar(
        select(Survey).where(
            Survey.id
            == answer.survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    if survey.status != "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se pueden corregir "
                "encuestas enviadas"
            ),
        )

    # --------------------------------------------------------
    # 4. VERSIÓN
    # --------------------------------------------------------

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == survey.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Versión de formulario no encontrada"
            ),
        )

    # --------------------------------------------------------
    # 5. FORMULARIO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 6. USUARIO QUE CORRIGE
    # --------------------------------------------------------

    correcting_user = current_user

    # --------------------------------------------------------
    # 7. ACCESO AL PROYECTO
    # --------------------------------------------------------

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id
            == correcting_user.id,
            UserProject.project_id
            == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    # --------------------------------------------------------
    # 8. MOTIVO
    # --------------------------------------------------------

    reason = answer_data.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Debe indicar el motivo "
                "de la corrección"
            ),
        )

    # --------------------------------------------------------
    # 9. VALIDAR NUEVO VALOR
    # --------------------------------------------------------

    new_values = validate_correction_value(
        field=field,
        answer_data=answer_data,
        db=db,
    )

    # --------------------------------------------------------
    # 10. VALOR ANTERIOR
    # --------------------------------------------------------

    old_values: AnswerValues = {
        "value_text": answer.value_text,
        "value_number": answer.value_number,
        "value_date": answer.value_date,
        "value_boolean": answer.value_boolean,
        "field_option_id": answer.field_option_id,
    }

    # --------------------------------------------------------
    # 11. DEBE EXISTIR UN CAMBIO REAL
    # --------------------------------------------------------

    if old_values == new_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El nuevo valor es igual "
                "al valor actual"
            ),
        )

    # --------------------------------------------------------
    # 12. REGISTRO DE AUDITORÍA
    # --------------------------------------------------------

    correction = SurveyAnswerCorrection(
        survey_answer_id=answer.id,
        corrected_by_user_id=(
            correcting_user.id
        ),

        old_value_text=(
            old_values["value_text"]
        ),
        old_value_number=(
            old_values["value_number"]
        ),
        old_value_date=(
            old_values["value_date"]
        ),
        old_value_boolean=(
            old_values["value_boolean"]
        ),
        old_field_option_id=(
            old_values["field_option_id"]
        ),

        new_value_text=(
            new_values["value_text"]
        ),
        new_value_number=(
            new_values["value_number"]
        ),
        new_value_date=(
            new_values["value_date"]
        ),
        new_value_boolean=(
            new_values["value_boolean"]
        ),
        new_field_option_id=(
            new_values["field_option_id"]
        ),

        reason=reason,
    )

    # --------------------------------------------------------
    # 13. ACTUALIZAR RESPUESTA
    # --------------------------------------------------------

    answer.value_text = (
        new_values["value_text"]
    )

    answer.value_number = (
        new_values["value_number"]
    )

    answer.value_date = (
        new_values["value_date"]
    )

    answer.value_boolean = (
        new_values["value_boolean"]
    )

    answer.field_option_id = (
        new_values["field_option_id"]
    )

    # --------------------------------------------------------
    # 14. TRANSACCIÓN ÚNICA
    # --------------------------------------------------------

    try:
        db.add(
            correction
        )

        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Error al guardar la corrección"
            ),
        )

    db.refresh(
        answer
    )

    db.refresh(
        correction
    )

    return {
        "answer": answer,
        "correction": correction,
    }


# ============================================================
# HISTORIAL DE CORRECCIONES
# ============================================================

@router.get(
    "/{answer_id}/corrections",
    response_model=list[
        SurveyAnswerCorrectionResponseSchema
    ],
    responses={
        404: {
            "description": (
                "Respuesta no encontrada"
            )
        }
    },
)
def get_answer_corrections(
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

    corrections = db.scalars(
        select(
            SurveyAnswerCorrection
        )
        .where(
            SurveyAnswerCorrection
            .survey_answer_id
            == answer_id
        )
        .order_by(
            SurveyAnswerCorrection.corrected_at,
            SurveyAnswerCorrection.id,
        )
    ).all()

    return corrections