from collections.abc import Generator

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.main import app
from backend.models import (
    Base,
    Role,
    User,
)
from backend.security import hash_password


# ============================================================
# BASE DE DATOS EXCLUSIVA PARA PRUEBAS
# ============================================================

TEST_DATABASE_URL = (
    "sqlite+pysqlite:///:memory:"
)


test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool,
)


@event.listens_for(
    test_engine,
    "connect",
)
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record,
) -> None:
    cursor = dbapi_connection.cursor()

    cursor.execute(
        "PRAGMA foreign_keys=ON"
    )

    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================
# DATOS DE PRUEBA
# ============================================================

TEST_EMPLOYEE_NUMBER = "TEST001"
TEST_IDENTIFICATION = "900000001"
TEST_PASSWORD = "PruebaSegura123*"


# ============================================================
# FIXTURE DE BASE DE DATOS
# ============================================================

@pytest.fixture()
def db() -> Generator[
    Session,
    None,
    None,
]:
    Base.metadata.create_all(
        bind=test_engine
    )

    session = TestingSessionLocal()

    try:
        role = Role(
            name="vendedor"
        )

        session.add(
            role
        )

        session.flush()

        user = User(
            employee_number=(
                TEST_EMPLOYEE_NUMBER
            ),
            identification=(
                TEST_IDENTIFICATION
            ),
            password_hash=hash_password(
                TEST_PASSWORD
            ),
            role_id=role.id,
            is_active=True,
        )

        session.add(
            user
        )

        session.commit()

        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=test_engine
        )


# ============================================================
# CLIENTE HTTP DE FASTAPI
# ============================================================

@pytest.fixture()
def client(
    db: Session,
) -> Generator[
    TestClient,
    None,
    None,
]:
    def override_get_db() -> Generator[
        Session,
        None,
        None,
    ]:
        test_db = (
            TestingSessionLocal()
        )

        try:
            yield test_db

        finally:
            test_db.close()

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(
        app
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()