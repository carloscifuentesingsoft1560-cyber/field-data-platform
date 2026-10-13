from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import User

from tests.conftest import (
    TEST_EMPLOYEE_NUMBER,
    TEST_PASSWORD,
)


WRONG_PASSWORD = (
    "Incorrecta123*"
)


# ============================================================
# FUNCIÓN AUXILIAR
# ============================================================

def get_test_user(
    db: Session,
) -> User:
    db.expire_all()

    user = db.scalar(
        select(User).where(
            User.employee_number
            == TEST_EMPLOYEE_NUMBER
        )
    )

    assert user is not None

    return user


# ============================================================
# LOGIN CORRECTO
# ============================================================

def test_login_with_valid_credentials(
    client,
):
    response = client.post(
        "/auth/login",
        json={
            "employee_number": (
                TEST_EMPLOYEE_NUMBER
            ),
            "password": (
                TEST_PASSWORD
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["token_type"]
        == "bearer"
    )

    assert (
        "access_token"
        in data
    )

    assert (
        data["access_token"]
    )


# ============================================================
# USUARIO INEXISTENTE
# ============================================================

def test_login_with_unknown_user_returns_401(
    client,
):
    response = client.post(
        "/auth/login",
        json={
            "employee_number": (
                "NO_EXISTE"
            ),
            "password": (
                WRONG_PASSWORD
            ),
        },
    )

    assert (
        response.status_code
        == 401
    )

    assert response.json() == {
        "detail": (
            "Número de empleado "
            "o contraseña incorrectos"
        )
    }


# ============================================================
# RF-09
# BLOQUEO DESPUÉS DE CINCO INTENTOS FALLIDOS
# ============================================================

def test_login_lockout_and_automatic_unlock(
    client,
    db: Session,
):
    # --------------------------------------------------------
    # INTENTOS 1 A 4
    # --------------------------------------------------------

    for attempt_number in range(
        1,
        5,
    ):
        response = client.post(
            "/auth/login",
            json={
                "employee_number": (
                    TEST_EMPLOYEE_NUMBER
                ),
                "password": (
                    WRONG_PASSWORD
                ),
            },
        )

        assert (
            response.status_code
            == 401
        ), (
            "Falló el intento "
            f"{attempt_number}"
        )

    user = get_test_user(
        db
    )

    assert (
        user.failed_login_attempts
        == 4
    )

    assert (
        user.locked_until
        is None
    )

    # --------------------------------------------------------
    # QUINTO INTENTO
    # --------------------------------------------------------

    response = client.post(
        "/auth/login",
        json={
            "employee_number": (
                TEST_EMPLOYEE_NUMBER
            ),
            "password": (
                WRONG_PASSWORD
            ),
        },
    )

    assert (
        response.status_code
        == 423
    )

    user = get_test_user(
        db
    )

    assert (
        user.failed_login_attempts
        == 5
    )

    assert (
        user.locked_until
        is not None
    )

    # --------------------------------------------------------
    # CONTRASEÑA CORRECTA DURANTE EL BLOQUEO
    # --------------------------------------------------------

    response = client.post(
        "/auth/login",
        json={
            "employee_number": (
                TEST_EMPLOYEE_NUMBER
            ),
            "password": (
                TEST_PASSWORD
            ),
        },
    )

    assert (
        response.status_code
        == 423
    )

    # --------------------------------------------------------
    # SIMULAR QUE LOS 15 MINUTOS YA PASARON
    # --------------------------------------------------------

    user = get_test_user(
        db
    )

    user.locked_until = (
        datetime.utcnow()
        - timedelta(
            minutes=1
        )
    )

    db.commit()

    # --------------------------------------------------------
    # LOGIN CORRECTO DESPUÉS DEL BLOQUEO
    # --------------------------------------------------------

    response = client.post(
        "/auth/login",
        json={
            "employee_number": (
                TEST_EMPLOYEE_NUMBER
            ),
            "password": (
                TEST_PASSWORD
            ),
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["token_type"]
        == "bearer"
    )

    assert (
        data["access_token"]
    )

    # --------------------------------------------------------
    # ESTADO FINAL
    # --------------------------------------------------------

    user = get_test_user(
        db
    )

    assert (
        user.failed_login_attempts
        == 0
    )

    assert (
        user.locked_until
        is None
    )