from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SurveyCreate(BaseModel):
    uuid: UUID
    form_version_id: int
    user_id: int

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180
    )

    captured_at: datetime


class SurveyUpdate(BaseModel):
    status: str | None = None


class SurveyResponse(BaseModel):
    id: int
    uuid: UUID
    form_version_id: int
    user_id: int
    status: str
    latitude: float | None
    longitude: float | None
    captured_at: datetime
    received_at: datetime

    model_config = {
        "from_attributes": True
    }