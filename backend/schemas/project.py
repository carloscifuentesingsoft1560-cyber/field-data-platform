from typing import Literal
from datetime import datetime

from pydantic import BaseModel, field_validator


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None 
    status:Literal ["active", "inactive"] = "active"

    @field_validator("name")
    @classmethod
    def validate_name (cls, value):
        if not value.strip():
            raise ValueError(
               "El nombre no puede estar vacio"
            )
        return value

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status:Literal ["active", "inactive"] 
    created_at:datetime
    updated_at: datetime
    

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: Literal ["active", "inactive"] | None = None 

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
