from pydantic import BaseModel, field_validator
from datetime import datetime

class UserCreate(BaseModel):
    employee_number: str
    identification: str
    password: str
    role_id: int
   

class UserResponse(BaseModel):
    id: int
    employee_number: str
    identification: str
    role_id: int
    is_active: bool
    created_at: datetime

class UserUpdate(BaseModel):
    employee_number:str | None = None
    identification: str | None = None
    role_id: int | None = None
    is_active:bool | None = None

    @field_validator(
        "employee_number",
        "identification",
        "role_id",
        "is_active"
    )
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("El campo no puede ser nulo")
        return value