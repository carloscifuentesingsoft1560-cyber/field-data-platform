from time import perf_counter

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.models import (
    Role,
    User,
)

from tests.conftest import (
    TEST_EMPLOYEE_NUMBER,
    TEST_PASSWORD,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

ADDITIONAL_USERS = 350

MAX_RESPONSE_TIME_SECONDS = 3.0


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

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


def create_capacity_users(
    db: Session,
) -> None:
    test_user = get_test_user(
        db
    )

    director_role = Role(
        name="director"
    )

    db.add(
        director_role
    )

    db.flush()

    # El usuario principal necesita un rol
    # de control para consultar /users.
    test_user.role_id = (
        director_role.id
    )

    # Reutilizamos el hash únicamente dentro
    # de esta base de pruebas.
    password_hash = (
        test_user.password_hash
    )

    users = []

    for index in range(
        1,
        ADDITIONAL_USERS + 1,
    ):
        user = User(
            employee_number=(
                f"LOAD{index:04d}"
            ),
            identification=(
                f"88{index:08d}"
            ),
            password_hash=(
                password_hash
            ),
            role_id=(
                director_role.id
            ),
            is_active=True,
        )

        users.append(
            user
        )

    db.add_all(
        users
    )

    db.commit()


def login_test_user(
    client,
) -> dict[str, str]:
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

    access_token = (
        response.json()[
            "access_token"
        ]
    )

    return {
        "Authorization": (
            f"Bearer {access_token}"
        )
    }


# ============================================================
# RNF-06
# MÁS DE 300 USUARIOS REGISTRADOS
# ============================================================

def test_platform_supports_more_than_300_users(
    db: Session,
):
    create_capacity_users(
        db
    )

    total_users = db.scalar(
        select(
            func.count(
                User.id
            )
        )
    )

    # 350 creados + TEST001
    assert (
        total_users
        == ADDITIONAL_USERS + 1
    )

    assert (
        total_users
        > 300
    )


# ============================================================
# RNF-07
# CONSULTA NORMAL <= 3 SEGUNDOS
# ============================================================

def test_user_listing_under_three_seconds(
    client,
    db: Session,
):
    create_capacity_users(
        db
    )

    headers = login_test_user(
        client
    )

    # --------------------------------------------------------
    # CALENTAMIENTO
    # --------------------------------------------------------

    warmup_response = client.get(
        "/users",
        headers=headers,
    )

    assert (
        warmup_response.status_code
        == 200
    )

    # --------------------------------------------------------
    # CINCO MEDICIONES
    # --------------------------------------------------------

    response_times = []

    for _ in range(
        5
    ):
        start_time = (
            perf_counter()
        )

        response = client.get(
            "/users",
            headers=headers,
        )

        end_time = (
            perf_counter()
        )

        elapsed = (
            end_time
            - start_time
        )

        assert (
            response.status_code
            == 200
        )

        assert (
            len(
                response.json()
            )
            == ADDITIONAL_USERS + 1
        )

        response_times.append(
            elapsed
        )

    slowest_response = max(
        response_times
    )

    assert (
        slowest_response
        <= MAX_RESPONSE_TIME_SECONDS
    ), (
        "La consulta más lenta tardó "
        f"{slowest_response:.4f} segundos"
    )