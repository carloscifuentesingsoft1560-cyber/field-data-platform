from typing import Literal

from pydantic import BaseModel


class FormFieldCreate(BaseModel):
    form_version_id: int
    name: str
    field_type: Literal[
        "text",
        "textarea",
        "number",
        "date",
        "boolean",
        "select"
    ]
    field_order: int
    is_required: bool = False

class FormFieldResponse(BaseModel):
    id: int
    form_version_id: int
    name: str
    field_type: str
    field_order: int
    is_required: bool

    model_config = {
        "from_attributes": True
    }