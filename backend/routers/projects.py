from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldOption,
    Form,
    FormField,
    FormVersion,
    Project,
    Survey,
    SurveyAnswer,
    SurveyAnswerCorrection,
    User,
    UserProject,
)
from backend.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from backend.security import (
    get_current_user,
    require_control_role,
    require_project_delete_role,
)


router = APIRouter()


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_project_access(
    project_id: int,
    current_user: User,
    db: Session,
) -> Project:
    """
    Valida que el proyecto exista y que el usuario
    autenticado esté asignado a él.
    """

    project = db.scalar(
        select(Project).where(
            Project.id == project_id
        )
    )

    if project is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Proyecto no encontrado"
            ),
        )

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id
            == current_user.id,
            UserProject.project_id
            == project.id,
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

    return project


# ============================================================
# CONSULTAR PROYECTOS DEL USUARIO
# ============================================================

@router.get(
    "/projects",
    response_model=list[
        ProjectResponse
    ],
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
    },
)
def get_projects(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    statement = (
        select(Project)
        .join(
            UserProject,
            UserProject.project_id
            == Project.id,
        )
        .where(
            UserProject.user_id
            == current_user.id
        )
        .order_by(
            Project.id
        )
    )

    projects = db.scalars(
        statement
    ).all()

    return projects


# ============================================================
# CREAR PROYECTO
# ============================================================

@router.post(
    "/projects",
    status_code=(
        status.HTTP_201_CREATED
    ),
    response_model=(
        ProjectResponse
    ),
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Rol no autorizado"
            )
        },
    },
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    db_project = Project(
        name=project.name,
        description=(
            project.description
        ),
        status=project.status,
        start_date=(
            project.start_date
        ),
        end_date=(
            project.end_date
        ),
    )

    db.add(
        db_project
    )

    db.flush()

    user_project = UserProject(
        user_id=(
            current_user.id
        ),
        project_id=(
            db_project.id
        ),
    )

    db.add(
        user_project
    )

    db.commit()

    db.refresh(
        db_project
    )

    return db_project


# ============================================================
# CONSULTAR UN PROYECTO
# ============================================================

@router.get(
    "/projects/{project_id}",
    response_model=(
        ProjectResponse
    ),
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
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
                "Proyecto no encontrado"
            )
        },
    },
)
def get_project(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    project = (
        validate_project_access(
            project_id=project_id,
            current_user=(
                current_user
            ),
            db=db,
        )
    )

    return project


# ============================================================
# ACTUALIZAR PROYECTO
# ============================================================

@router.patch(
    "/projects/{project_id}",
    response_model=(
        ProjectResponse
    ),
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Rol no autorizado o usuario "
                "sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Proyecto no encontrado"
            )
        },
        422: {
            "description": (
                "Fechas de proyecto inválidas"
            )
        },
    },
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    project = (
        validate_project_access(
            project_id=project_id,
            current_user=(
                current_user
            ),
            db=db,
        )
    )

    update_data = (
        project_data.model_dump(
            exclude_unset=True
        )
    )

    new_start_date = (
        update_data.get(
            "start_date",
            project.start_date,
        )
    )

    new_end_date = (
        update_data.get(
            "end_date",
            project.end_date,
        )
    )

    if (
        new_end_date is not None
        and new_end_date
        < new_start_date
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "La fecha de finalización "
                "no puede ser anterior a "
                "la fecha de inicio"
            ),
        )

    for (
        field,
        value,
    ) in update_data.items():
        setattr(
            project,
            field,
            value,
        )

    db.commit()

    db.refresh(
        project
    )

    return project


# ============================================================
# ELIMINAR PROYECTO DEFINITIVAMENTE
# DIRECTOR / JEFE NACIONAL
# ============================================================

@router.delete(
    "/projects/{project_id}",
    responses={
        200: {
            "description": (
                "Proyecto y datos asociados "
                "eliminados correctamente"
            )
        },
        400: {
            "description": (
                "Confirmación de eliminación "
                "incorrecta"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Solo Director o Jefe Nacional "
                "pueden eliminar proyectos"
            )
        },
        404: {
            "description": (
                "Proyecto no encontrado"
            )
        },
    },
)
def delete_project(
    project_id: int,
    confirmation: str = Query(
        ...,
        description=(
            "Nombre exacto del proyecto "
            "como confirmación"
        ),
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_project_delete_role
    ),
):
    project = (
        validate_project_access(
            project_id=project_id,
            current_user=(
                current_user
            ),
            db=db,
        )
    )

    # --------------------------------------------------------
    # CONFIRMACIÓN FINAL
    # --------------------------------------------------------

    if (
        confirmation.strip()
        != project.name.strip()
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La confirmación no coincide "
                "con el nombre del proyecto"
            ),
        )

    try:
        # ----------------------------------------------------
        # IDENTIFICAR FORMULARIOS
        # ----------------------------------------------------

        form_ids = list(
            db.scalars(
                select(Form.id).where(
                    Form.project_id
                    == project.id
                )
            ).all()
        )

        # ----------------------------------------------------
        # IDENTIFICAR VERSIONES
        # ----------------------------------------------------

        if form_ids:
            version_ids = list(
                db.scalars(
                    select(
                        FormVersion.id
                    ).where(
                        FormVersion.form_id.in_(
                            form_ids
                        )
                    )
                ).all()
            )
        else:
            version_ids = []

        # ----------------------------------------------------
        # IDENTIFICAR CAMPOS
        # ----------------------------------------------------

        if version_ids:
            field_ids = list(
                db.scalars(
                    select(
                        FormField.id
                    ).where(
                        FormField
                        .form_version_id
                        .in_(
                            version_ids
                        )
                    )
                ).all()
            )
        else:
            field_ids = []

        # ----------------------------------------------------
        # IDENTIFICAR ENCUESTAS
        # ----------------------------------------------------

        if version_ids:
            survey_ids = list(
                db.scalars(
                    select(
                        Survey.id
                    ).where(
                        Survey
                        .form_version_id
                        .in_(
                            version_ids
                        )
                    )
                ).all()
            )
        else:
            survey_ids = []

        # ----------------------------------------------------
        # IDENTIFICAR RESPUESTAS
        # ----------------------------------------------------

        if survey_ids:
            answer_ids = list(
                db.scalars(
                    select(
                        SurveyAnswer.id
                    ).where(
                        SurveyAnswer
                        .survey_id
                        .in_(
                            survey_ids
                        )
                    )
                ).all()
            )
        else:
            answer_ids = []

        # ----------------------------------------------------
        # 1. HISTORIAL DE CORRECCIONES
        # ----------------------------------------------------

        if answer_ids:
            db.execute(
                delete(
                    SurveyAnswerCorrection
                ).where(
                    SurveyAnswerCorrection
                    .survey_answer_id
                    .in_(
                        answer_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 2. RESPUESTAS
        # ----------------------------------------------------

        if survey_ids:
            db.execute(
                delete(
                    SurveyAnswer
                ).where(
                    SurveyAnswer
                    .survey_id
                    .in_(
                        survey_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 3. ENCUESTAS
        # ----------------------------------------------------

        if version_ids:
            db.execute(
                delete(
                    Survey
                ).where(
                    Survey
                    .form_version_id
                    .in_(
                        version_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 4. OPCIONES DE CAMPOS
        # ----------------------------------------------------

        if field_ids:
            db.execute(
                delete(
                    FieldOption
                ).where(
                    FieldOption
                    .form_field_id
                    .in_(
                        field_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 5. CAMPOS
        # ----------------------------------------------------

        if version_ids:
            db.execute(
                delete(
                    FormField
                ).where(
                    FormField
                    .form_version_id
                    .in_(
                        version_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 6. VERSIONES
        # ----------------------------------------------------

        if form_ids:
            db.execute(
                delete(
                    FormVersion
                ).where(
                    FormVersion
                    .form_id
                    .in_(
                        form_ids
                    )
                )
            )

        # ----------------------------------------------------
        # 7. FORMULARIOS
        # ----------------------------------------------------

        db.execute(
            delete(
                Form
            ).where(
                Form.project_id
                == project.id
            )
        )

        # ----------------------------------------------------
        # 8. ASIGNACIONES DE USUARIOS
        # ----------------------------------------------------

        db.execute(
            delete(
                UserProject
            ).where(
                UserProject.project_id
                == project.id
            )
        )

        # ----------------------------------------------------
        # 9. PROYECTO
        # ----------------------------------------------------

        db.delete(
            project
        )

        # TODO SE CONFIRMA EN UNA SOLA TRANSACCIÓN.
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": (
            "Proyecto y todos sus datos "
            "asociados fueron eliminados "
            "definitivamente"
        ),
        "deleted": {
            "forms":
                len(form_ids),

            "versions":
                len(version_ids),

            "fields":
                len(field_ids),

            "surveys":
                len(survey_ids),

            "answers":
                len(answer_ids),
        },
    }