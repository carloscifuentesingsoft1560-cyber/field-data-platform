from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Survey,
    SurveyAnswer,
    FormVersion,
    Form,
    FormField,
    FieldOption,
    User,
    UserProject,
)
from backend.schemas.survey import (
    SurveyCreate,
    SurveyResponse,
)

from backend.schemas.survey_sync import (
    SurveySyncCreate,
    SurveySyncResponse,
)


router = APIRouter(
    prefix="/surveys",
    tags=["surveys"],
)


@router.post(
    "/",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": SurveyResponse,
            "description": "La encuesta ya había sido procesada y se devuelve la existente",
        },
        400: {
            "description": "Versión no publicada, formulario inactivo o usuario inactivo",
        },
        403: {
            "description": "El usuario no está asignado al proyecto",
        },
        404: {
            "description": "Versión, formulario o usuario no encontrado",
        },
    },
    
)
def create_survey(
    survey_data: SurveyCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    # 1. Verificar si este UUID ya fue procesado
    existing_survey = db.scalar(
        select(Survey).where(
            Survey.uuid == survey_data.uuid
        )
    )

    if existing_survey is not None:
        response.status_code = status.HTTP_200_OK
        return existing_survey

    # 2. Verificar que la versión del formulario exista
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == survey_data.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada",
        )

    # 3. Solo se pueden diligenciar versiones publicadas
    if version.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden diligenciar versiones publicadas",
        )

    # 4. Buscar el formulario
    form = db.scalar(
        select(Form).where(
            Form.id == version.form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
        )

    # Verificar que el formulario esté activo
    if not form.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formulario no está activo",
        )

    # 5. Verificar que el usuario exista
    user = db.scalar(
        select(User).where(
            User.id == survey_data.user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no está activo",
        )

    # 6. Verificar asignación usuario-proyecto
    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id == survey_data.user_id,
            UserProject.project_id == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este proyecto",
        )

    # 7. Crear la encuesta
    new_survey = Survey(
        uuid=survey_data.uuid,
        form_version_id=survey_data.form_version_id,
        user_id=survey_data.user_id,
        status="submitted",
        latitude=survey_data.latitude,
        longitude=survey_data.longitude,
        captured_at=survey_data.captured_at,
    )

    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)

    # MUY IMPORTANTE:
    # La función debe devolver el objeto creado.
    return new_survey

@router.get(
    "/",
    response_model=list[SurveyResponse],
)
def get_surveys(
    db: Session = Depends(get_db),
):
    surveys = db.scalars(
        select(Survey).order_by(
            Survey.received_at.desc()
        )
    ).all()

    return surveys


@router.get(
    "/by-uuid/{survey_uuid}",
    response_model=SurveyResponse,
    responses={
        404: {
            "description": "Encuesta no encontrada"
        }
    },
)
def get_survey_by_uuid(
    survey_uuid: UUID,
    db: Session = Depends(get_db),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.uuid == survey_uuid
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    return survey


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    responses={
        404: {
            "description": "Encuesta no encontrada"
        }
    },
)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.id == survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encuesta no encontrada",
        )

    return survey

@router.post(
    "/sync",
    response_model=SurveySyncResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "description": "La encuesta ya había sido sincronizada"
        },
        400: {
            "description": "Datos de encuesta o respuestas inválidos"
        },
        403: {
            "description": "Usuario sin acceso al proyecto"
        },
        404: {
            "description": "Versión, formulario, usuario o campo no encontrado"
        },
    },
)
def sync_survey(
    sync_data: SurveySyncCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    # 1. Verificar si esta encuesta ya fue sincronizada
    #    UUID funciona como identificador único generado por el dispositivo.
    existing_survey = db.scalar(
        select(Survey).where(
            Survey.uuid == sync_data.uuid
        )
    )

    if existing_survey is not None:
        existing_answers = db.scalars(
            select(SurveyAnswer)
            .where(
                SurveyAnswer.survey_id == existing_survey.id
            )
            .order_by(SurveyAnswer.id)
        ).all()

        response.status_code = status.HTTP_200_OK

        return {
            "survey": existing_survey,
            "answers": existing_answers,
        }

    # 2. Verificar que la versión del formulario exista
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == sync_data.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada",
        )

    # 3. Solo se pueden diligenciar versiones publicadas
    if version.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden sincronizar versiones publicadas",
        )

    # 4. Obtener el formulario
    form = db.scalar(
        select(Form).where(
            Form.id == version.form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
        )

    # 5. El formulario debe estar activo
    if not form.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formulario no está activo",
        )

    # 6. Verificar que el usuario exista
    user = db.scalar(
        select(User).where(
            User.id == sync_data.user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # 7. El usuario debe estar activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no está activo",
        )

    # 8. Verificar que el usuario pertenezca al proyecto
    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id == sync_data.user_id,
            UserProject.project_id == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este proyecto",
        )

    # 9. Obtener todos los campos de la versión
    fields = db.scalars(
        select(FormField).where(
            FormField.form_version_id == version.id
        )
    ).all()

    fields_by_id = {
        field.id: field
        for field in fields
    }

    # 10. Obtener los IDs de campos enviados por el dispositivo
    answer_field_ids = [
        answer.form_field_id
        for answer in sync_data.answers
    ]

    # 11. No permitir el mismo campo dos veces
    if len(answer_field_ids) != len(set(answer_field_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede responder dos veces el mismo campo",
        )

    # 12. Todos los campos enviados deben pertenecer
    #     a la misma versión del formulario
    for answer in sync_data.answers:
        if answer.form_field_id not in fields_by_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo {answer.form_field_id} no pertenece "
                    "a la versión del formulario"
                ),
            )

    # 13. Verificar campos obligatorios
    required_field_ids = {
        field.id
        for field in fields
        if field.is_required
    }

    submitted_field_ids = set(answer_field_ids)

    missing_required = (
        required_field_ids - submitted_field_ids
    )

    if missing_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Faltan campos obligatorios: "
                + ", ".join(
                    str(field_id)
                    for field_id in sorted(missing_required)
                )
            ),
        )

    # 14. Validar el tipo de cada respuesta
    for answer in sync_data.answers:
        field = fields_by_id[answer.form_field_id]

        # TEXT / TEXTAREA
        if field.field_type in ("text", "textarea"):
            if answer.value_text is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} requiere value_text",
                )

            if (
                answer.value_number is not None
                or answer.value_date is not None
                or answer.value_boolean is not None
                or answer.field_option_id is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} solo admite value_text",
                )

        # NUMBER
        elif field.field_type == "number":
            if answer.value_number is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} requiere value_number",
                )

            if (
                answer.value_text is not None
                or answer.value_date is not None
                or answer.value_boolean is not None
                or answer.field_option_id is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} solo admite value_number",
                )

        # DATE
        elif field.field_type == "date":
            if answer.value_date is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} requiere value_date",
                )

            if (
                answer.value_text is not None
                or answer.value_number is not None
                or answer.value_boolean is not None
                or answer.field_option_id is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} solo admite value_date",
                )

        # BOOLEAN
        elif field.field_type == "boolean":
            if answer.value_boolean is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} requiere value_boolean",
                )

            if (
                answer.value_text is not None
                or answer.value_number is not None
                or answer.value_date is not None
                or answer.field_option_id is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} solo admite value_boolean",
                )

        # SELECT
        elif field.field_type == "select":
            if answer.field_option_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} requiere field_option_id",
                )

            option = db.scalar(
                select(FieldOption).where(
                    FieldOption.id == answer.field_option_id,
                    FieldOption.form_field_id == field.id,
                )
            )

            if option is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"La opción seleccionada no pertenece "
                        f"al campo {field.id}"
                    ),
                )

            if (
                answer.value_text is not None
                or answer.value_number is not None
                or answer.value_date is not None
                or answer.value_boolean is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo {field.id} solo admite field_option_id",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tipo de campo no soportado: "
                    f"{field.field_type}"
                ),
            )

    # 15. Crear la encuesta.
    #     Todavía NO hacemos commit.
    new_survey = Survey(
        uuid=sync_data.uuid,
        form_version_id=sync_data.form_version_id,
        user_id=sync_data.user_id,
        status="submitted",
        latitude=sync_data.latitude,
        longitude=sync_data.longitude,
        captured_at=sync_data.captured_at,
    )

    db.add(new_survey)

    # flush envía el INSERT a PostgreSQL y permite obtener
    # new_survey.id, pero SIN cerrar la transacción.
    db.flush()

    # 16. Crear todas las respuestas
    new_answers = []

    for answer in sync_data.answers:
        new_answer = SurveyAnswer(
            survey_id=new_survey.id,
            form_field_id=answer.form_field_id,
            value_text=answer.value_text,
            value_number=answer.value_number,
            value_date=answer.value_date,
            value_boolean=answer.value_boolean,
            field_option_id=answer.field_option_id,
        )

        db.add(new_answer)
        new_answers.append(new_answer)

    # 17. Un solo COMMIT para Survey + SurveyAnswers
    db.commit()

    # 18. Refrescar objetos antes de devolverlos
    db.refresh(new_survey)

    for answer in new_answers:
        db.refresh(answer)

    return {
        "survey": new_survey,
        "answers": new_answers,
    }