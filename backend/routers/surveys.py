from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import (
    and_,
    select,
)
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldOption,
    Form,
    FormField,
    FormVersion,
    Survey,
    SurveyAnswer,
    SurveyAnswerCorrection,
    User,
    UserProject,
)
from backend.schemas.survey import (
    SurveyResponse,
)
from backend.schemas.survey_detail import (
    SurveyDetailResponse,
)
from backend.schemas.survey_sync import (
    SurveySyncCreate,
    SurveySyncResponse,
)
from backend.security import (
    get_current_user,
)


router = APIRouter(
    prefix="/surveys",
    tags=["surveys"],
    dependencies=[
        Depends(get_current_user)
    ],
)


# ============================================================
# VALIDAR ACCESO AL PROYECTO DE UNA ENCUESTA
# ============================================================

def get_survey_project_context(
    survey: Survey,
    current_user: User,
    db: Session,
) -> tuple[
    FormVersion,
    Form,
]:
    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == survey.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    form = db.scalar(
        select(Form).where(
            Form.id == version.form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Formulario no encontrado"
            ),
        )

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id
            == current_user.id,
            UserProject.project_id
            == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    return version, form


# ============================================================
# LISTAR ENCUESTAS
# ============================================================

@router.get(
    "/",
    response_model=list[
        SurveyResponse
    ],
)
def get_surveys(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    surveys = db.scalars(
        select(Survey)
        .join(
            FormVersion,
            Survey.form_version_id
            == FormVersion.id,
        )
        .join(
            Form,
            FormVersion.form_id
            == Form.id,
        )
        .join(
            UserProject,
            UserProject.project_id
            == Form.project_id,
        )
        .where(
            UserProject.user_id
            == current_user.id
        )
        .order_by(
            Survey.received_at.desc()
        )
    ).all()

    return surveys


# ============================================================
# BUSCAR ENCUESTA POR UUID
# ============================================================

@router.get(
    "/by-uuid/{survey_uuid}",
    response_model=SurveyResponse,
    responses={
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Encuesta no encontrada"
            )
        },
    },
)
def get_survey_by_uuid(
    survey_uuid: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.uuid
            == survey_uuid
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Encuesta no encontrada"
            ),
        )

    get_survey_project_context(
        survey=survey,
        current_user=current_user,
        db=db,
    )

    return survey


# ============================================================
# SINCRONIZAR ENCUESTA
# ============================================================

@router.post(
    "/sync",
    response_model=SurveySyncResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    responses={
        200: {
            "description": (
                "La encuesta ya había "
                "sido sincronizada"
            )
        },
        400: {
            "description": (
                "Datos de encuesta o "
                "respuestas inválidos"
            )
        },
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Versión, formulario "
                "o campo no encontrado"
            )
        },
        409: {
            "description": (
                "Conflicto de UUID"
            )
        },
    },
)
def sync_survey(
    sync_data: SurveySyncCreate,
    response: Response,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    # --------------------------------------------------------
    # 1. IDEMPOTENCIA POR UUID
    # --------------------------------------------------------

    existing_survey = db.scalar(
        select(Survey).where(
            Survey.uuid
            == sync_data.uuid
        )
    )

    if existing_survey is not None:
        if (
            existing_survey.user_id
            != current_user.id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El UUID ya está asociado "
                    "a otra encuesta"
                ),
            )

        get_survey_project_context(
            survey=existing_survey,
            current_user=current_user,
            db=db,
        )

        existing_answers = db.scalars(
            select(SurveyAnswer)
            .where(
                SurveyAnswer.survey_id
                == existing_survey.id
            )
            .order_by(
                SurveyAnswer.id
            )
        ).all()

        response.status_code = (
            status.HTTP_200_OK
        )

        return {
            "survey": existing_survey,
            "answers": existing_answers,
        }

    # --------------------------------------------------------
    # 2. VERSIÓN
    # --------------------------------------------------------

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == sync_data.form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Versión de formulario "
                "no encontrada"
            ),
        )

    if (
        version.status
        != "published"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Solo se pueden sincronizar "
                "versiones publicadas"
            ),
        )

    # --------------------------------------------------------
    # 3. FORMULARIO
    # --------------------------------------------------------

    form = db.scalar(
        select(Form).where(
            Form.id
            == version.form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Formulario no encontrado"
            ),
        )

    if not form.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "El formulario no está activo"
            ),
        )

    # --------------------------------------------------------
    # 4. USUARIO AUTENTICADO
    # --------------------------------------------------------

    user = current_user

    # --------------------------------------------------------
    # 5. ASIGNACIÓN AL PROYECTO
    # --------------------------------------------------------

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id
            == user.id,
            UserProject.project_id
            == form.project_id,
        )
    )

    if user_project is None:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    # --------------------------------------------------------
    # 6. CAMPOS DE LA VERSIÓN
    # --------------------------------------------------------

    fields = db.scalars(
        select(FormField).where(
            FormField.form_version_id
            == version.id
        )
    ).all()

    fields_by_id = {
        field.id: field
        for field in fields
    }

    answer_field_ids = [
        answer.form_field_id
        for answer in sync_data.answers
    ]

    # --------------------------------------------------------
    # 7. CAMPOS DUPLICADOS
    # --------------------------------------------------------

    if (
        len(answer_field_ids)
        != len(
            set(answer_field_ids)
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "No se puede responder "
                "dos veces el mismo campo"
            ),
        )

    # --------------------------------------------------------
    # 8. CAMPOS PERTENECEN A LA VERSIÓN
    # --------------------------------------------------------

    for answer in (
        sync_data.answers
    ):
        if (
            answer.form_field_id
            not in fields_by_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    f"El campo "
                    f"{answer.form_field_id} "
                    "no pertenece a la versión "
                    "del formulario"
                ),
            )

    # --------------------------------------------------------
    # 9. CAMPOS OBLIGATORIOS
    # --------------------------------------------------------

    required_field_ids = {
        field.id
        for field in fields
        if field.is_required
    }

    submitted_field_ids = set(
        answer_field_ids
    )

    missing_required = (
        required_field_ids
        - submitted_field_ids
    )

    if missing_required:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Faltan campos obligatorios: "
                + ", ".join(
                    str(field_id)
                    for field_id
                    in sorted(
                        missing_required
                    )
                )
            ),
        )

    # --------------------------------------------------------
    # 10. VALIDAR TIPOS
    # --------------------------------------------------------

    for answer in (
        sync_data.answers
    ):
        field = fields_by_id[
            answer.form_field_id
        ]

        # ----------------------------------------------------
        # TEXT / TEXTAREA
        # ----------------------------------------------------

        if field.field_type in (
            "text",
            "textarea",
        ):
            if (
                answer.value_text
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "requiere value_text"
                    ),
                )

            if (
                answer.value_number
                is not None
                or answer.value_date
                is not None
                or answer.value_boolean
                is not None
                or answer.field_option_id
                is not None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "solo admite value_text"
                    ),
                )

        # ----------------------------------------------------
        # NUMBER
        # ----------------------------------------------------

        elif (
            field.field_type
            == "number"
        ):
            if (
                answer.value_number
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "requiere value_number"
                    ),
                )

            if (
                answer.value_text
                is not None
                or answer.value_date
                is not None
                or answer.value_boolean
                is not None
                or answer.field_option_id
                is not None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "solo admite value_number"
                    ),
                )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        elif (
            field.field_type
            == "date"
        ):
            if (
                answer.value_date
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "requiere value_date"
                    ),
                )

            if (
                answer.value_text
                is not None
                or answer.value_number
                is not None
                or answer.value_boolean
                is not None
                or answer.field_option_id
                is not None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "solo admite value_date"
                    ),
                )

        # ----------------------------------------------------
        # BOOLEAN
        # ----------------------------------------------------

        elif (
            field.field_type
            == "boolean"
        ):
            if (
                answer.value_boolean
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "requiere value_boolean"
                    ),
                )

            if (
                answer.value_text
                is not None
                or answer.value_number
                is not None
                or answer.value_date
                is not None
                or answer.field_option_id
                is not None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "solo admite value_boolean"
                    ),
                )

        # ----------------------------------------------------
        # SELECT
        # ----------------------------------------------------

        elif (
            field.field_type
            == "select"
        ):
            if (
                answer.field_option_id
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "requiere field_option_id"
                    ),
                )

            option = db.scalar(
                select(FieldOption).where(
                    FieldOption.id
                    == answer.field_option_id,
                    FieldOption.form_field_id
                    == field.id,
                )
            )

            if option is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La opción seleccionada "
                        "no pertenece al campo "
                        f"{field.id}"
                    ),
                )

            if (
                answer.value_text
                is not None
                or answer.value_number
                is not None
                or answer.value_date
                is not None
                or answer.value_boolean
                is not None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        f"El campo {field.id} "
                        "solo admite "
                        "field_option_id"
                    ),
                )

        # ----------------------------------------------------
        # TIPO NO SOPORTADO
        # ----------------------------------------------------

        else:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Tipo de campo "
                    "no soportado: "
                    f"{field.field_type}"
                ),
            )

    # --------------------------------------------------------
    # 11. CREAR ENCUESTA
    # --------------------------------------------------------

    new_survey = Survey(
        uuid=sync_data.uuid,
        form_version_id=(
            sync_data.form_version_id
        ),
        user_id=user.id,
        status="submitted",
        latitude=(
            sync_data.latitude
        ),
        longitude=(
            sync_data.longitude
        ),
        captured_at=(
            sync_data.captured_at
        ),
    )

    db.add(
        new_survey
    )

    new_answers = []

    try:
        db.flush()

        for answer in (
            sync_data.answers
        ):
            new_answer = (
                SurveyAnswer(
                    survey_id=(
                        new_survey.id
                    ),
                    form_field_id=(
                        answer.form_field_id
                    ),
                    value_text=(
                        answer.value_text
                    ),
                    value_number=(
                        answer.value_number
                    ),
                    value_date=(
                        answer.value_date
                    ),
                    value_boolean=(
                        answer.value_boolean
                    ),
                    field_option_id=(
                        answer.field_option_id
                    ),
                )
            )

            db.add(
                new_answer
            )

            new_answers.append(
                new_answer
            )

        db.commit()

    except IntegrityError:
        db.rollback()

        existing_survey = db.scalar(
            select(Survey).where(
                Survey.uuid
                == sync_data.uuid
            )
        )

        if (
            existing_survey
            is not None
        ):
            if (
                existing_survey.user_id
                != current_user.id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "El UUID ya está "
                        "asociado a otra encuesta"
                    ),
                )

            get_survey_project_context(
                survey=existing_survey,
                current_user=(
                    current_user
                ),
                db=db,
            )

            existing_answers = (
                db.scalars(
                    select(
                        SurveyAnswer
                    )
                    .where(
                        SurveyAnswer.survey_id
                        == existing_survey.id
                    )
                    .order_by(
                        SurveyAnswer.id
                    )
                ).all()
            )

            response.status_code = (
                status.HTTP_200_OK
            )

            return {
                "survey": (
                    existing_survey
                ),
                "answers": (
                    existing_answers
                ),
            }

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Conflicto de integridad "
                "al sincronizar la encuesta"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Error al guardar "
                "la encuesta"
            ),
        )

    db.refresh(
        new_survey
    )

    for answer in new_answers:
        db.refresh(
            answer
        )

    return {
        "survey": new_survey,
        "answers": new_answers,
    }


# ============================================================
# DETALLE COMPLETO DE ENCUESTA
# ============================================================

@router.get(
    "/{survey_id}/detail",
    response_model=(
        SurveyDetailResponse
    ),
    responses={
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Encuesta no encontrada"
            )
        },
    },
)
def get_survey_detail(
    survey_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    # --------------------------------------------------------
    # 1. ENCUESTA
    # --------------------------------------------------------

    survey = db.scalar(
        select(Survey).where(
            Survey.id
            == survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Encuesta no encontrada"
            ),
        )

    # --------------------------------------------------------
    # 2. VERSIÓN + FORMULARIO + ACCESO
    # --------------------------------------------------------

    (
        version,
        form,
    ) = get_survey_project_context(
        survey=survey,
        current_user=current_user,
        db=db,
    )

    # --------------------------------------------------------
    # 3. USUARIO QUE DILIGENCIÓ
    # --------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id
            == survey.user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Usuario no encontrado"
            ),
        )

    # --------------------------------------------------------
    # 4. CAMPOS + RESPUESTAS + OPCIÓN
    # --------------------------------------------------------

    rows = db.execute(
        select(
            FormField,
            SurveyAnswer,
            FieldOption,
        )
        .outerjoin(
            SurveyAnswer,
            and_(
                SurveyAnswer.form_field_id
                == FormField.id,
                SurveyAnswer.survey_id
                == survey.id,
            ),
        )
        .outerjoin(
            FieldOption,
            SurveyAnswer.field_option_id
            == FieldOption.id,
        )
        .where(
            FormField.form_version_id
            == survey.form_version_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    # --------------------------------------------------------
    # 5. IDS DE RESPUESTAS
    # --------------------------------------------------------

    answer_ids = [
        answer.id
        for (
            field,
            answer,
            option,
        ) in rows
        if answer is not None
    ]

    # --------------------------------------------------------
    # 6. CORRECCIONES
    # --------------------------------------------------------

    corrections_by_answer_id = {}

    if answer_ids:
        corrections = db.scalars(
            select(
                SurveyAnswerCorrection
            )
            .where(
                SurveyAnswerCorrection
                .survey_answer_id
                .in_(answer_ids)
            )
            .order_by(
                SurveyAnswerCorrection
                .corrected_at,
                SurveyAnswerCorrection.id,
            )
        ).all()

        for correction in corrections:
            correction_list = (
                corrections_by_answer_id
                .setdefault(
                    correction
                    .survey_answer_id,
                    [],
                )
            )

            correction_list.append(
                correction
            )

    # --------------------------------------------------------
    # 7. CONSTRUIR DETALLE
    # --------------------------------------------------------

    answers = []

    for (
        field,
        answer,
        option,
    ) in rows:
        if answer is not None:
            answer_corrections = (
                corrections_by_answer_id
                .get(
                    answer.id,
                    [],
                )
            )
        else:
            answer_corrections = []

        answers.append(
            {
                "answer_id": (
                    answer.id
                    if answer is not None
                    else None
                ),

                "form_field_id": (
                    field.id
                ),

                "field_name": (
                    field.name
                ),

                "field_type": (
                    field.field_type
                ),

                "field_order": (
                    field.field_order
                ),

                "is_required": (
                    field.is_required
                ),

                "answered": (
                    answer is not None
                ),

                "value_text": (
                    answer.value_text
                    if answer is not None
                    else None
                ),

                "value_number": (
                    answer.value_number
                    if answer is not None
                    else None
                ),

                "value_date": (
                    answer.value_date
                    if answer is not None
                    else None
                ),

                "value_boolean": (
                    answer.value_boolean
                    if answer is not None
                    else None
                ),

                "field_option_id": (
                    answer.field_option_id
                    if answer is not None
                    else None
                ),

                "option_label": (
                    option.label
                    if option is not None
                    else None
                ),

                "option_value": (
                    option.value
                    if option is not None
                    else None
                ),

                "was_corrected": (
                    len(
                        answer_corrections
                    ) > 0
                ),

                "correction_count": (
                    len(
                        answer_corrections
                    )
                ),

                "corrections": (
                    answer_corrections
                ),
            }
        )

    # --------------------------------------------------------
    # 8. RESPUESTA COMPLETA
    # --------------------------------------------------------

    return {
        "id": survey.id,
        "uuid": survey.uuid,

        "project_id": (
            form.project_id
        ),

        "form_id": (
            form.id
        ),

        "form_name": (
            form.name
        ),

        "form_version_id": (
            version.id
        ),

        "version_number": (
            version.version_number
        ),

        "user_id": (
            user.id
        ),

        "employee_number": (
            user.employee_number
        ),

        "status": (
            survey.status
        ),

        "latitude": (
            survey.latitude
        ),

        "longitude": (
            survey.longitude
        ),

        "captured_at": (
            survey.captured_at
        ),

        "received_at": (
            survey.received_at
        ),

        "answers": answers,
    }


# ============================================================
# CONSULTAR ENCUESTA
# ============================================================

@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    responses={
        403: {
            "description": (
                "Usuario sin acceso "
                "al proyecto"
            )
        },
        404: {
            "description": (
                "Encuesta no encontrada"
            )
        },
    },
)
def get_survey(
    survey_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    survey = db.scalar(
        select(Survey).where(
            Survey.id
            == survey_id
        )
    )

    if survey is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Encuesta no encontrada"
            ),
        )

    get_survey_project_context(
        survey=survey,
        current_user=current_user,
        db=db,
    )

    return survey