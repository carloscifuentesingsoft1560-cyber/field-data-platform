from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.survey import SurveyResponse
from backend.schemas.survey_answer import (
    SurveyAnswerResponse,
)


class SurveySyncAnswerCreate(BaseModel):
    form_field_id: int

    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    field_option_id: int | None = None


class SurveySyncCreate(BaseModel):
    uuid: UUID
    form_version_id: int

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    captured_at: datetime

    answers: list[
        SurveySyncAnswerCreate
    ]


class SurveySyncResponse(BaseModel):
    survey: SurveyResponse

    answers: list[
        SurveyAnswerResponse
    ]