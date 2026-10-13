from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import (
    Project,
    User,
    UserProject,
)

from tests.conftest import (
    TEST_EMPLOYEE_NUMBER,
    TEST_PASSWORD,
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

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

    token = response.json()[
        "access_token"
    ]

    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


def create_project(
    db: Session,
    name: str,
) -> Project:
    project = Project(
        name=name,
        description=(
            f"Proyecto de prueba {name}"
        ),
        status="active",
        start_date=date(
            2026,
            1,
            1,
        ),
        end_date=date(
            2026,
            12,
            31,
        ),
    )

    db.add(
        project
    )

    db.flush()

    return project


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
# RF-04
# SIN AUTENTICACIÓN NO SE PUEDEN CONSULTAR PROYECTOS
# ============================================================

def test_projects_require_authentication(
    client,
):
    response = client.get(
        "/projects"
    )

    assert (
        response.status_code
        == 401
    )


# ============================================================
# RF-04
# LISTAR SOLAMENTE PROYECTOS ASIGNADOS
# ============================================================

def test_user_only_lists_assigned_projects(
    client,
    db: Session,
):
    user = get_test_user(
        db
    )

    assigned_project = create_project(
        db,
        "Proyecto asignado",
    )

    create_project(
        db,
        "Proyecto no asignado",
    )

    assignment = UserProject(
        user_id=user.id,
        project_id=(
            assigned_project.id
        ),
    )

    db.add(
        assignment
    )

    db.commit()

    headers = login_test_user(
        client
    )

    response = client.get(
        "/projects",
        headers=headers,
    )

    assert (
        response.status_code
        == 200
    )

    projects = response.json()

    assert len(projects) == 1

    assert (
        projects[0]["id"]
        == assigned_project.id
    )

    assert (
        projects[0]["name"]
        == "Proyecto asignado"
    )


# ============================================================
# RF-04
# CONSULTAR PROYECTO ASIGNADO
# ============================================================

def test_user_can_access_assigned_project(
    client,
    db: Session,
):
    user = get_test_user(
        db
    )

    project = create_project(
        db,
        "Proyecto permitido",
    )

    assignment = UserProject(
        user_id=user.id,
        project_id=project.id,
    )

    db.add(
        assignment
    )

    db.commit()

    headers = login_test_user(
        client
    )

    response = client.get(
        f"/projects/{project.id}",
        headers=headers,
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.json()["id"]
        == project.id
    )


# ============================================================
# RF-04
# DENEGAR PROYECTO NO ASIGNADO
# ============================================================

def test_user_cannot_access_unassigned_project(
    client,
    db: Session,
):
    project = create_project(
        db,
        "Proyecto restringido",
    )

    db.commit()

    headers = login_test_user(
        client
    )

    response = client.get(
        f"/projects/{project.id}",
        headers=headers,
    )

    assert (
        response.status_code
        == 403
    )

    assert response.json() == {
        "detail": (
            "El usuario no está asignado "
            "a este proyecto"
        )
    }


# ============================================================
# CONTROL POR ROL
# VENDEDOR NO PUEDE MODIFICAR PROYECTOS
# ============================================================

def test_operational_user_cannot_update_project(
    client,
    db: Session,
):
    user = get_test_user(
        db
    )

    project = create_project(
        db,
        "Proyecto sin edición",
    )

    assignment = UserProject(
        user_id=user.id,
        project_id=project.id,
    )

    db.add(
        assignment
    )

    db.commit()

    headers = login_test_user(
        client
    )

    response = client.patch(
        f"/projects/{project.id}",
        headers=headers,
        json={
            "name": (
                "Intento de modificación"
            )
        },
    )

    assert (
        response.status_code
        == 403
    )
    