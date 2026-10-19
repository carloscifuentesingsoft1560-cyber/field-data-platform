from datetime import datetime

from pydantic import (
    BaseModel,
    field_validator,
)


class UserCreate(BaseModel):
    employee_number: str
    identification: str
    password: str
    role_id: int

    @field_validator(
        "employee_number",
        "identification",
    )
    @classmethod
    def validate_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "El campo no puede estar vacío"
            )

        return value

    @field_validator(
        "password"
    )
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        if len(value) < 8:
            raise ValueError(
                "La contraseña debe tener "
                "al menos 8 caracteres"
            )

        return value


class UserResponse(BaseModel):
    id: int
    employee_number: str
    identification: str
    role_id: int
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    employee_number: str | None = None
    identification: str | None = None
    role_id: int | None = None
    is_active: bool | None = None

    @field_validator(
        "employee_number",
        "identification",
        "role_id",
        "is_active",
    )
    @classmethod
    def reject_null(
        cls,
        value,
    ):
        if value is None:
            raise ValueError(
                "El campo no puede ser nulo"
            )

        return value


class UserPasswordReset(
    BaseModel
):
    new_password: str

    @field_validator(
        "new_password"
    )
    @classmethod
    def validate_new_password(
        cls,
        value: str,
    ) -> str:
        if len(value) < 8:
            raise ValueError(
                "La nueva contraseña debe "
                "tener al menos 8 caracteres"
            )

        return value