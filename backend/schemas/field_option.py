from pydantic import BaseModel

class FieldOptionCreate(BaseModel):
    form_field_id: int
    label: str
    value: str
    option_order: int

class FieldOptionUpdate(BaseModel):
    label: str | None = None
    value: str | None = None
    option_order: int | None = None

class FieldOptionResponse(BaseModel):
    id: int
    form_field_id: int
    label: str
    value: str
    option_order: int

    model_config= {
        "from_attributes": True
    }

    


