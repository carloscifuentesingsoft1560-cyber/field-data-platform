from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ============================================================
# CREACIÓN DE RESPUESTA
# ============================================================

class SurveyAnswerCreate(BaseModel):
    survey_id: int
    form_field_id: int

    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    field_option_id: int | None = None


# ============================================================
# CORRECCIÓN DE RESPUESTA
# ============================================================

class SurveyAnswerUpdate(BaseModel):
    corrected_by_user_id: int
    reason: str

    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    field_option_id: int | None = None


# ============================================================
# RESPUESTA NORMAL
# ============================================================

class SurveyAnswerResponse(BaseModel):
    id: int
    survey_id: int
    form_field_id: int

    value_text: str | None
    value_number: Decimal | None
    value_date: date | None
    value_boolean: bool | None
    field_option_id: int | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ============================================================
# HISTORIAL DE CORRECCIÓN
# ============================================================

class SurveyAnswerCorrectionResponse(BaseModel):
    id: int
    survey_answer_id: int
    corrected_by_user_id: int

    old_value_text: str | None
    old_value_number: Decimal | None
    old_value_date: date | None
    old_value_boolean: bool | None
    old_field_option_id: int | None

    new_value_text: str | None
    new_value_number: Decimal | None
    new_value_date: date | None
    new_value_boolean: bool | None
    new_field_option_id: int | None

    reason: str | None
    corrected_at: datetime

    model_config = {
        "from_attributes": True
    }


# ============================================================
# RESULTADO DEL PATCH
# ============================================================

class SurveyAnswerCorrectionResult(BaseModel):
    answer: SurveyAnswerResponse
    correction: SurveyAnswerCorrectionResponse