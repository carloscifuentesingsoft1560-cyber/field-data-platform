from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SurveyAnswerCreate(BaseModel):
    survey_id: int
    form_field_id: int

    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    field_option_id: int | None = None


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