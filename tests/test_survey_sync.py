from datetime import date
from uuid import uuid4

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.models import (
    Form,
    FormField,
    FormVersion,
    Project,
    Survey,
    SurveyAnswer,
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


def create_sync_structure(
    db: Session,
    assign_user: bool = True,
) -> tuple[
    Project,
    Form,
    FormVersion,
    FormField,
]:
    user = get_test_user(
        db
    )

    project = Project(
        name="Proyecto sincronización",
        description=(
            "Proyecto para pruebas "
            "de sincronización"
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

    form = Form(
        project_id=project.id,
        name="Formulario de prueba",
        description=(
            "Formulario para pruebas"
        ),
        is_active=True,
    )

    db.add(
        form
    )

    db.flush()

    version = FormVersion(
        form_id=form.id,
        version_number=1,
        status="published",
    )

    db.add(
        version
    )

    db.flush()

    field = FormField(
        form_version_id=version.id,
        name="Nombre del establecimiento",
        field_type="text",
        field_order=1,
        is_required=True,
    )

    db.add(
        field
    )

    if assign_user:
        assignment = UserProject(
            user_id=user.id,
            project_id=project.id,
        )

        db.add(
            assignment
        )

    db.commit()

    return (
        project,
        form,
        version,
        field,
    )


def build_sync_payload(
    version: FormVersion,
    field: FormField,
    survey_uuid: str,
) -> dict:
    return {
        "uuid": survey_uuid,
        "form_version_id": (
            version.id
        ),
        "latitude": 4.609710,
        "longitude": -74.081750,
        "captured_at": (
            "2026-10-13T15:30:00"
        ),
        "answers": [
            {
                "form_field_id": (
                    field.id
                ),
                "value_text": (
                    "Tienda de prueba"
                ),
                "value_number": None,
                "value_date": None,
                "value_boolean": None,
                "field_option_id": None,
            }
        ],
    }


# ============================================================
# RF-06
# SINCRONIZACIÓN EXITOSA
# ============================================================

def test_sync_creates_survey_and_answers(
    client,
    db: Session,
):
    (
        project,
        form,
        version,
        field,
    ) = create_sync_structure(
        db
    )

    headers = login_test_user(
        client
    )

    survey_uuid = str(
        uuid4()
    )

    payload = build_sync_payload(
        version=version,
        field=field,
        survey_uuid=survey_uuid,
    )

    response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
    )

    assert (
        response.status_code
        == 201
    )

    data = response.json()

    assert (
        data["survey"]["uuid"]
        == survey_uuid
    )

    assert (
        data["survey"]["form_version_id"]
        == version.id
    )

    assert (
        data["survey"]["status"]
        == "submitted"
    )

    assert (
        len(
            data["answers"]
        )
        == 1
    )

    assert (
        data["answers"][0][
            "form_field_id"
        ]
        == field.id
    )

    assert (
        data["answers"][0][
            "value_text"
        ]
        == "Tienda de prueba"
    )

    db.expire_all()

    survey_count = db.scalar(
        select(
            func.count(
                Survey.id
            )
        )
    )

    answer_count = db.scalar(
        select(
            func.count(
                SurveyAnswer.id
            )
        )
    )

    assert survey_count == 1
    assert answer_count == 1


# ============================================================
# RF-06 / RNF-05
# MISMO UUID NO DEBE CREAR DUPLICADOS
# ============================================================

def test_sync_same_uuid_is_idempotent(
    client,
    db: Session,
):
    (
        project,
        form,
        version,
        field,
    ) = create_sync_structure(
        db
    )

    headers = login_test_user(
        client
    )

    survey_uuid = str(
        uuid4()
    )

    payload = build_sync_payload(
        version=version,
        field=field,
        survey_uuid=survey_uuid,
    )

    first_response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
    )

    assert (
        first_response.status_code
        == 201
    )

    first_data = (
        first_response.json()
    )

    first_survey_id = (
        first_data["survey"]["id"]
    )

    second_response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
    )

    assert (
        second_response.status_code
        == 200
    )

    second_data = (
        second_response.json()
    )

    assert (
        second_data["survey"]["id"]
        == first_survey_id
    )

    assert (
        second_data["survey"]["uuid"]
        == survey_uuid
    )

    db.expire_all()

    survey_count = db.scalar(
        select(
            func.count(
                Survey.id
            )
        )
    )

    answer_count = db.scalar(
        select(
            func.count(
                SurveyAnswer.id
            )
        )
    )

    assert survey_count == 1
    assert answer_count == 1


# ============================================================
# RF-04 / RF-06
# NO SINCRONIZAR PROYECTO NO ASIGNADO
# ============================================================

def test_sync_rejects_unassigned_project(
    client,
    db: Session,
):
    (
        project,
        form,
        version,
        field,
    ) = create_sync_structure(
        db,
        assign_user=False,
    )

    headers = login_test_user(
        client
    )

    payload = build_sync_payload(
        version=version,
        field=field,
        survey_uuid=str(
            uuid4()
        ),
    )

    response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
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

    db.expire_all()

    survey_count = db.scalar(
        select(
            func.count(
                Survey.id
            )
        )
    )

    assert survey_count == 0


# ============================================================
# RNF-05
# NO GUARDAR ENCUESTA SI HAY CAMPOS DUPLICADOS
# ============================================================

def test_sync_rejects_duplicate_field_answers(
    client,
    db: Session,
):
    (
        project,
        form,
        version,
        field,
    ) = create_sync_structure(
        db
    )

    headers = login_test_user(
        client
    )

    payload = build_sync_payload(
        version=version,
        field=field,
        survey_uuid=str(
            uuid4()
        ),
    )

    payload["answers"].append(
        {
            "form_field_id": (
                field.id
            ),
            "value_text": (
                "Segunda respuesta"
            ),
            "value_number": None,
            "value_date": None,
            "value_boolean": None,
            "field_option_id": None,
        }
    )

    response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "No se puede responder "
            "dos veces el mismo campo"
        )
    }

    db.expire_all()

    survey_count = db.scalar(
        select(
            func.count(
                Survey.id
            )
        )
    )

    answer_count = db.scalar(
        select(
            func.count(
                SurveyAnswer.id
            )
        )
    )

    assert survey_count == 0
    assert answer_count == 0


# ============================================================
# RF-06
# CAMPOS OBLIGATORIOS DEBEN ESTAR PRESENTES
# ============================================================

def test_sync_rejects_missing_required_field(
    client,
    db: Session,
):
    (
        project,
        form,
        version,
        field,
    ) = create_sync_structure(
        db
    )

    headers = login_test_user(
        client
    )

    payload = {
        "uuid": str(
            uuid4()
        ),
        "form_version_id": (
            version.id
        ),
        "latitude": 4.609710,
        "longitude": -74.081750,
        "captured_at": (
            "2026-10-13T15:30:00"
        ),
        "answers": [],
    }

    response = client.post(
        "/surveys/sync",
        headers=headers,
        json=payload,
    )

    assert (
        response.status_code
        == 400
    )

    assert (
        response.json()["detail"]
        == (
            "Faltan campos obligatorios: "
            f"{field.id}"
        )
    )

    db.expire_all()

    survey_count = db.scalar(
        select(
            func.count(
                Survey.id
            )
        )
    )

    assert survey_count == 0