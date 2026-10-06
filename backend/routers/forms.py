from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Form,
    Project,
    User,
    UserProject,
)
from backend.schemas.form import (
    FormCreate,
    FormResponse,
    FormUpdate,
)
from backend.security import (
    get_current_user,
    require_control_role,
)


router = APIRouter(
    prefix="/forms",
    tags=["forms"],
    dependencies=[
        Depends(get_current_user)
    ],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_project_access(
    project_id: int,
    current_user: User,
    db: Session,
) -> Project:
    """
    Comprueba que el proyecto exista y que
    el usuario esté asignado a él.
    """

    project = db.scalar(
        select(Project).where(
            Project.id == project_id
        )
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    return project


def validate_form_access(
    form_id: int,
    current_user: User,
    db: Session,
) -> Form:
    """
    Comprueba que el formulario exista y que
    el usuario esté asignado al proyecto
    al que pertenece.
    """

    form = db.scalar(
        select(Form).where(
            Form.id == form_id
        )
    )

    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no está asignado "
                "a este proyecto"
            ),
        )

    return form


# ============================================================
# CREAR FORMULARIO
# ============================================================

@router.post(
    "/",
    response_model=FormResponse,
    status_code=status.HTTP_201_CREATED,
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
    },
)
def create_form(
    form: FormCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    validate_project_access(
        project_id=form.project_id,
        current_user=current_user,
        db=db,
    )

    db_form = Form(
        project_id=form.project_id,
        name=form.name,
        description=form.description,
    )

    db.add(
        db_form
    )

    db.commit()

    db.refresh(
        db_form
    )

    return db_form


# ============================================================
# CONSULTAR FORMULARIOS DEL USUARIO
# ============================================================

@router.get(
    "/",
    response_model=list[
        FormResponse
    ],
    responses={
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
    },
)
def get_forms(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    forms = db.scalars(
        select(Form)
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
            Form.id
        )
    ).all()

    return forms


# ============================================================
# CONSULTAR UN FORMULARIO
# ============================================================

@router.get(
    "/{form_id}",
    response_model=FormResponse,
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
                "Formulario no encontrado"
            )
        },
    },
)
def get_form(
    form_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    form = validate_form_access(
        form_id=form_id,
        current_user=current_user,
        db=db,
    )

    return form


# ============================================================
# ACTUALIZAR FORMULARIO
# ============================================================

@router.patch(
    "/{form_id}",
    response_model=FormResponse,
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
                "Formulario no encontrado"
            )
        },
    },
)
def update_form(
    form_id: int,
    form_data: FormUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    form = validate_form_access(
        form_id=form_id,
        current_user=current_user,
        db=db,
    )

    update_data = (
        form_data.model_dump(
            exclude_unset=True
        )
    )

    for field, value in (
        update_data.items()
    ):
        setattr(
            form,
            field,
            value,
        )

    db.commit()

    db.refresh(
        form
    )

    return form