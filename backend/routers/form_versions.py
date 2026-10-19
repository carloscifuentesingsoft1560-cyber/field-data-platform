from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldOption,
    Form,
    FormField,
    FormVersion,
    User,
    UserProject,
)
from backend.schemas.form_version import (
    FormVersionCreate,
    FormVersionResponse,
)
from backend.security import (
    get_current_user,
    require_control_role,
)


router = APIRouter(
    prefix="/form-versions",
    tags=["form-versions"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_form_access(
    form_id: int,
    current_user: User,
    db: Session,
) -> Form:
    """
    Valida que el formulario exista y que el usuario
    autenticado esté asignado al proyecto al que
    pertenece el formulario.
    """

    form = db.scalar(
        select(Form).where(
            Form.id == form_id
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

    return form


def validate_version_access(
    version_id: int,
    current_user: User,
    db: Session,
) -> FormVersion:
    """
    Valida que la versión exista y que el usuario
    tenga acceso al proyecto del formulario
    al que pertenece la versión.
    """

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id
            == version_id
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

    validate_form_access(
        form_id=version.form_id,
        current_user=current_user,
        db=db,
    )

    return version


def clone_published_version(
    source_version: FormVersion,
    target_version: FormVersion,
    db: Session,
) -> None:
    """
    Copia los campos y opciones de la versión
    publicada hacia una nueva versión borrador.
    """

    source_fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == source_version.id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    for source_field in source_fields:
        new_field = FormField(
            form_version_id=(
                target_version.id
            ),
            name=(
                source_field.name
            ),
            field_type=(
                source_field.field_type
            ),
            field_order=(
                source_field.field_order
            ),
            is_required=(
                source_field.is_required
            ),
        )

        db.add(
            new_field
        )

        # Necesitamos el ID del campo nuevo
        # antes de copiar sus opciones.
        db.flush()

        source_options = db.scalars(
            select(FieldOption)
            .where(
                FieldOption.form_field_id
                == source_field.id
            )
            .order_by(
                FieldOption.option_order
            )
        ).all()

        for (
            source_option
        ) in source_options:
            new_option = FieldOption(
                form_field_id=(
                    new_field.id
                ),
                label=(
                    source_option.label
                ),
                value=(
                    source_option.value
                ),
                option_order=(
                    source_option
                    .option_order
                ),
            )

            db.add(
                new_option
            )


# ============================================================
# CREAR VERSIÓN DE FORMULARIO
# ============================================================

@router.post(
    "/",
    response_model=(
        FormVersionResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
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
                "Formulario no encontrado"
            )
        },
        409: {
            "description": (
                "Ya existe una versión "
                "en borrador"
            )
        },
    },
)
def create_form_version(
    version_data: FormVersionCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    validate_form_access(
        form_id=(
            version_data.form_id
        ),
        current_user=current_user,
        db=db,
    )

    # --------------------------------------------------------
    # SOLO UN BORRADOR POR FORMULARIO
    # --------------------------------------------------------

    existing_draft = db.scalar(
        select(FormVersion).where(
            FormVersion.form_id
            == version_data.form_id,
            FormVersion.status
            == "draft",
        )
    )

    if (
        existing_draft
        is not None
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ya existe una versión "
                "en borrador para este "
                "formulario"
            ),
        )

    # --------------------------------------------------------
    # CALCULAR SIGUIENTE NÚMERO
    # --------------------------------------------------------

    last_version = db.scalar(
        select(
            func.max(
                FormVersion
                .version_number
            )
        ).where(
            FormVersion.form_id
            == version_data.form_id
        )
    )

    next_version = (
        last_version or 0
    ) + 1

    new_version = FormVersion(
        form_id=(
            version_data.form_id
        ),
        version_number=(
            next_version
        ),
        status="draft",
    )

    db.add(
        new_version
    )

    # Obtenemos el ID sin cerrar
    # la transacción.
    db.flush()

    # --------------------------------------------------------
    # COPIAR LA VERSIÓN PUBLICADA
    # --------------------------------------------------------

    published_version = db.scalar(
        select(FormVersion).where(
            FormVersion.form_id
            == version_data.form_id,
            FormVersion.status
            == "published",
            FormVersion.id
            != new_version.id,
        )
    )

    if (
        published_version
        is not None
    ):
        clone_published_version(
            source_version=(
                published_version
            ),
            target_version=(
                new_version
            ),
            db=db,
        )

    db.commit()

    db.refresh(
        new_version
    )

    return new_version


# ============================================================
# CONSULTAR VERSIONES DE UN FORMULARIO
# ============================================================

@router.get(
    "/form/{form_id}",
    response_model=list[
        FormVersionResponse
    ],
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
def get_form_versions(
    form_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    validate_form_access(
        form_id=form_id,
        current_user=current_user,
        db=db,
    )

    versions = db.scalars(
        select(FormVersion)
        .where(
            FormVersion.form_id
            == form_id
        )
        .order_by(
            FormVersion.version_number
        )
    ).all()

    return versions


# ============================================================
# PUBLICAR VERSIÓN
# ============================================================

@router.patch(
    "/{version_id}/publish",
    response_model=(
        FormVersionResponse
    ),
    responses={
        400: {
            "description": (
                "Versión no publicable"
            )
        },
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
                "Versión de formulario "
                "no encontrada"
            )
        },
    },
)
def publish_form_version(
    version_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_control_role
    ),
):
    version = (
        validate_version_access(
            version_id=version_id,
            current_user=current_user,
            db=db,
        )
    )

    # --------------------------------------------------------
    # SOLO SE PUBLICAN BORRADORES
    # --------------------------------------------------------

    if (
        version.status
        != "draft"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Solo se puede publicar "
                "una versión en borrador"
            ),
        )

    # --------------------------------------------------------
    # DEBE TENER AL MENOS UN CAMPO
    # --------------------------------------------------------

    fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == version.id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    if (
        len(fields) == 0
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "No se puede publicar "
                "una versión sin campos"
            ),
        )

    # --------------------------------------------------------
    # LOS SELECT DEBEN TENER OPCIONES
    # --------------------------------------------------------

    for field in fields:
        if (
            field.field_type
            != "select"
        ):
            continue

        existing_option = db.scalar(
            select(FieldOption.id)
            .where(
                FieldOption
                .form_field_id
                == field.id
            )
        )

        if (
            existing_option
            is None
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "El campo "
                    f"'{field.name}' "
                    "debe tener al menos "
                    "una opción antes de "
                    "publicar"
                ),
            )

    # --------------------------------------------------------
    # ARCHIVAR VERSIÓN PUBLICADA ANTERIOR
    # --------------------------------------------------------

    published_version = db.scalar(
        select(FormVersion).where(
            FormVersion.form_id
            == version.form_id,
            FormVersion.status
            == "published",
            FormVersion.id
            != version.id,
        )
    )

    if (
        published_version
        is not None
    ):
        published_version.status = (
            "archived"
        )

    # --------------------------------------------------------
    # PUBLICAR NUEVA VERSIÓN
    # --------------------------------------------------------

    version.status = (
        "published"
    )

    db.commit()

    db.refresh(
        version
    )

    return version