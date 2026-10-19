from datetime import (
    datetime,
    timedelta,
)

import pytest

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import (
    Role,
    User,
)
from backend.security import (
    hash_password,
)

from tests.conftest import (
    TEST_EMPLOYEE_NUMBER,
    TEST_PASSWORD,
)


NEW_PASSWORD = (
    "NuevaSegura456*"
)

ADMIN_PASSWORD = (
    "AdminSegura789*"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def create_control_user(
    db: Session,
    role_name: str,
    username: str,
) -> User:
    role = Role(
        name=role_name
    )

    db.add(
        role
    )

    db.flush()

    user = User(
        employee_number=username,
        identification=(
            f"ID-{username}"
        ),
        password_hash=(
            hash_password(
                ADMIN_PASSWORD
            )
        ),
        role_id=role.id,
        is_active=True,
    )

    db.add(
        user
    )

    db.commit()

    db.refresh(
        user
    )

    return user


def login_user(
    client,
    username: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={
            "employee_number":
                username,
            "password":
                password,
        },
    )

    assert (
        response.status_code
        == 200
    )

    token = response.json()[
        "access_token"
    ]

    return {
        "Authorization":
            f"Bearer {token}"
    }


def get_test_user(
    db: Session,
) -> User:
    user = db.scalar(
        select(User).where(
            User.employee_number
            == TEST_EMPLOYEE_NUMBER
        )
    )

    assert user is not None

    return user


# ============================================================
# DIRECTOR Y JEFE NACIONAL
# PUEDEN RESTABLECER CONTRASEÑAS
# ============================================================

@pytest.mark.parametrize(
    (
        "role_name",
        "username",
    ),
    [
        (
            "director",
            "DIRECTOR_TEST",
        ),
        (
            "jefe_nacional",
            "JEFE_TEST",
        ),
    ],
)
def test_authorized_roles_can_reset_password(
    client,
    db: Session,
    role_name: str,
    username: str,
):
    administrator = (
        create_control_user(
            db,
            role_name,
            username,
        )
    )

    target_user = get_test_user(
        db
    )

    # Simulamos también una cuenta
    # bloqueada para comprobar que
    # el restablecimiento la desbloquea.
    target_user.failed_login_attempts = 5
    target_user.locked_until = (
        datetime.utcnow()
        + timedelta(
            minutes=15
        )
    )

    db.commit()

    headers = login_user(
        client,
        administrator
        .employee_number,
        ADMIN_PASSWORD,
    )

    response = client.patch(
        (
            f"/users/"
            f"{target_user.id}"
            "/reset-password"
        ),
        headers=headers,
        json={
            "new_password":
                NEW_PASSWORD,
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "message": (
            "Contraseña restablecida "
            "correctamente"
        )
    }

    db.expire_all()

    refreshed_user = (
        get_test_user(
            db
        )
    )

    assert (
        refreshed_user
        .failed_login_attempts
        == 0
    )

    assert (
        refreshed_user
        .locked_until
        is None
    )

    # La contraseña anterior
    # ya no debe funcionar.
    old_password_response = (
        client.post(
            "/auth/login",
            json={
                "employee_number":
                    TEST_EMPLOYEE_NUMBER,
                "password":
                    TEST_PASSWORD,
            },
        )
    )

    assert (
        old_password_response
        .status_code
        == 401
    )

    # La contraseña nueva
    # sí debe funcionar.
    new_password_response = (
        client.post(
            "/auth/login",
            json={
                "employee_number":
                    TEST_EMPLOYEE_NUMBER,
                "password":
                    NEW_PASSWORD,
            },
        )
    )

    assert (
        new_password_response
        .status_code
        == 200
    )


# ============================================================
# COORDINADOR
# NO PUEDE RESTABLECER CONTRASEÑAS
# ============================================================

def test_coordinator_cannot_reset_password(
    client,
    db: Session,
):
    coordinator = (
        create_control_user(
            db,
            "coordinador",
            "COORD_TEST",
        )
    )

    target_user = get_test_user(
        db
    )

    headers = login_user(
        client,
        coordinator
        .employee_number,
        ADMIN_PASSWORD,
    )

    response = client.patch(
        (
            f"/users/"
            f"{target_user.id}"
            "/reset-password"
        ),
        headers=headers,
        json={
            "new_password":
                NEW_PASSWORD,
        },
    )

    assert (
        response.status_code
        == 403
    )


# ============================================================
# UN ADMINISTRADOR NO PUEDE USAR
# ESTA FUNCIÓN SOBRE SÍ MISMO
# ============================================================

def test_admin_cannot_reset_own_password(
    client,
    db: Session,
):
    director = (
        create_control_user(
            db,
            "director",
            "DIRECTOR_SELF",
        )
    )

    headers = login_user(
        client,
        director
        .employee_number,
        ADMIN_PASSWORD,
    )

    response = client.patch(
        (
            f"/users/"
            f"{director.id}"
            "/reset-password"
        ),
        headers=headers,
        json={
            "new_password":
                NEW_PASSWORD,
        },
    )

    assert (
        response.status_code
        == 400
    )