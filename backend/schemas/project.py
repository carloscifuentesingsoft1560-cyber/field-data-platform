from typing import Literal
from datetime import date, datetime

from pydantic import BaseModel, field_validator
from pydantic import model_validator


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None 
    status:Literal ["active", "inactive"] = "active"
    start_date: date
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name (cls, value):
        if not value.strip():
            raise ValueError(
               "El nombre no puede estar vacio"
            )
        return value
    @model_validator(mode="after")
    def validate_dates (self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(
                "La fecha de finalizacion no puede ser anterior a la fecha de inicio."
            )
        return self
    
class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status:Literal ["active", "inactive"] 
    created_at:datetime
    updated_at: datetime
    start_date: date
    end_date: date | None
    

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: Literal ["active", "inactive"] | None = None 
    start_date: date |None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name (cls, value):
        if value is None:
            raise ValueError("El nombre no puede ser nulo")
      
        if not value.strip():
            raise ValueError(
                "El nombre no puede estar vacio"
            )
        return value
    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value):
        if value is None:
            raise ValueError(
                "La fecha de inicio no puede ser nula"
            )
        return value
