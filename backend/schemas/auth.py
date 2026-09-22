from pydantic import BaseModel


class LoginRequest(BaseModel):
    employee_number: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class AuthMeResponse(BaseModel):
    id: int
    employee_number: str
    identification: str
    role_id: int
    role_name: str
    is_active: bool