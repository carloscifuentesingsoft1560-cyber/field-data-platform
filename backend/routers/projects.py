from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Form,
    Project,
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
                "Project not found"
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

    # Obtenemos el ID antes del commit
    # para crear la asignación
    # UserProject.
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

    # Proyecto y asignación se guardan
    # dentro de la misma transacción.
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
                "Project not found"
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
                "Project not found"
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
                "La fecha de finalizacion "
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
# ELIMINAR PROYECTO
# ============================================================

@router.delete(
    "/projects/{project_id}",
    responses={
        200: {
            "description": (
                "Proyecto eliminado correctamente"
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
                "Project not found"
            )
        },
        409: {
            "description": (
                "El proyecto tiene formularios "
                "asociados y no puede eliminarse"
            )
        },
    },
)
def delete_project(
    project_id: int,
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
    # NO PERMITIR ELIMINAR PROYECTOS CON FORMULARIOS
    # --------------------------------------------------------

    existing_form = db.scalar(
        select(Form.id).where(
            Form.project_id
            == project.id
        )
    )

    if (
        existing_form
        is not None
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "No se puede eliminar el proyecto "
                "porque tiene formularios asociados"
            ),
        )

    # --------------------------------------------------------
    # ELIMINAR ASIGNACIONES USER_PROJECT
    # --------------------------------------------------------

    db.execute(
        delete(
            UserProject
        ).where(
            UserProject.project_id
            == project.id
        )
    )

    # --------------------------------------------------------
    # ELIMINAR PROYECTO
    # --------------------------------------------------------

    db.delete(
        project
    )

    db.commit()

    return {
        "message":
            "Project deleted"
    }