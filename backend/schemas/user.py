from pydantic import BaseModel
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
