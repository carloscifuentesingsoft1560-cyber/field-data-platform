from pydantic import BaseModel
from datetime import datetime



class FormCreate(BaseModel):
    project_id: int
    name: str
    description: str | None = None

class FormResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None
    is_active: bool
    created_at : datetime

class FormUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None 