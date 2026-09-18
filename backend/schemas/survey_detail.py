from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.survey_answer import (
    SurveyAnswerCorrectionResponse,
)


class SurveyDetailAnswer(BaseModel):
    answer_id: int | None

    form_field_id: int
    field_name: str
    field_type: str
    field_order: int
    is_required: bool

    answered: bool

    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None

    field_option_id: int | None = None
    option_label: str | None = None
    option_value: str | None = None

    was_corrected: bool = False
    correction_count: int = 0

    corrections: list[
        SurveyAnswerCorrectionResponse
    ] = Field(
        default_factory=list
    )


class SurveyDetailResponse(BaseModel):
    id: int
    uuid: UUID

    project_id: int

    form_id: int
    form_name: str

    form_version_id: int
    version_number: int

    user_id: int
    employee_number: str

    status: str

    latitude: float | None
    longitude: float | None

    captured_at: datetime
    received_at: datetime

    answers: list[SurveyDetailAnswer]