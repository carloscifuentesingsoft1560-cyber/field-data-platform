import csv
from io import BytesIO, StringIO

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldOption,
    Form,
    FormField,
    FormVersion,
    Survey,
    SurveyAnswer,
    User,
    UserProject,
)
from backend.security import get_current_user


router = APIRouter(
    prefix="/exports",
    tags=["exports"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_answer_export_value(
    answer: SurveyAnswer | None,
    option: FieldOption | None,
):
    """
    Convierte una respuesta en un valor adecuado
    para exportación CSV.
    """

    if answer is None:
        return ""

    if answer.field_option_id is not None:
        if option is not None:
            return option.label

        return str(answer.field_option_id)

    if answer.value_text is not None:
        return answer.value_text

    if answer.value_number is not None:
        return str(answer.value_number)

    if answer.value_date is not None:
        return answer.value_date.isoformat()

    if answer.value_boolean is not None:
        return (
            "true"
            if answer.value_boolean
            else "false"
        )

    return ""


def get_export_data(
    form_version_id: int,
    current_user: User,
    db: Session,
):
    """
    Obtiene los datos necesarios para exportar
    una versión de formulario.

    Antes de acceder a las encuestas valida que
    el usuario autenticado esté asignado al proyecto.
    """

    # --------------------------------------------------------
    # 1. VERSIÓN DEL FORMULARIO
    # --------------------------------------------------------

    version = db.scalar(
        select(FormVersion).where(
            FormVersion.id == form_version_id
        )
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versión de formulario no encontrada",
        )

    # --------------------------------------------------------
    # 2. FORMULARIO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 3. VALIDAR ACCESO AL PROYECTO
    # --------------------------------------------------------

    user_project = db.scalar(
        select(UserProject).where(
            UserProject.user_id == current_user.id,
            UserProject.project_id == form.project_id,
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

    # --------------------------------------------------------
    # 4. CAMPOS DE LA VERSIÓN
    # --------------------------------------------------------

    fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id
            == form_version_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    # --------------------------------------------------------
    # 5. ENCUESTAS ENVIADAS
    # --------------------------------------------------------

    survey_rows = db.execute(
        select(
            Survey,
            User,
        )
        .join(
            User,
            Survey.user_id == User.id,
        )
        .where(
            Survey.form_version_id
            == form_version_id,
            Survey.status == "submitted",
        )
        .order_by(
            Survey.received_at
        )
    ).all()

    survey_ids = [
        survey.id
        for survey, user in survey_rows
    ]

    # --------------------------------------------------------
    # 6. RESPUESTAS
    # --------------------------------------------------------

    answers_by_survey_and_field = {}

    if survey_ids:
        answer_rows = db.execute(
            select(
                SurveyAnswer,
                FieldOption,
            )
            .outerjoin(
                FieldOption,
                SurveyAnswer.field_option_id
                == FieldOption.id,
            )
            .where(
                SurveyAnswer.survey_id.in_(
                    survey_ids
                )
            )
        ).all()

        for answer, option in answer_rows:
            answers_by_survey_and_field[
                (
                    answer.survey_id,
                    answer.form_field_id,
                )
            ] = (
                answer,
                option,
            )

    return (
        version,
        form,
        fields,
        survey_rows,
        answers_by_survey_and_field,
    )


# ============================================================
# EXPORTACIÓN CSV
# ============================================================

@router.get(
    "/form-versions/{form_version_id}/csv",
    responses={
        200: {
            "description": (
                "Archivo CSV generado correctamente"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Usuario sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Versión o formulario no encontrado"
            )
        },
    },
)
def export_form_version_csv(
    form_version_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    (
        version,
        form,
        fields,
        survey_rows,
        answers_by_survey_and_field,
    ) = get_export_data(
        form_version_id=form_version_id,
        current_user=current_user,
        db=db,
    )

    output = StringIO(
        newline=""
    )

    writer = csv.writer(
        output,
        delimiter=";",
        lineterminator="\n",
    )

    # --------------------------------------------------------
    # ENCABEZADOS GENERALES
    # --------------------------------------------------------

    headers = [
        "survey_id",
        "uuid",
        "project_id",
        "form_id",
        "form_version_id",
        "version_number",
        "user_id",
        "employee_number",
        "status",
        "captured_at",
        "received_at",
        "latitude",
        "longitude",
    ]

    field_headers = [
        f"field_{field.id}_{field.name}"
        for field in fields
    ]

    writer.writerow(
        headers + field_headers
    )

    # --------------------------------------------------------
    # FILAS
    # --------------------------------------------------------

    for survey, user in survey_rows:
        row = [
            survey.id,
            str(survey.uuid),
            form.project_id,
            form.id,
            version.id,
            version.version_number,
            user.id,
            user.employee_number,
            survey.status,
            survey.captured_at.isoformat(),
            survey.received_at.isoformat(),

            (
                str(
                    survey.latitude
                ).replace(
                    ".",
                    ",",
                )
                if survey.latitude is not None
                else ""
            ),

            (
                str(
                    survey.longitude
                ).replace(
                    ".",
                    ",",
                )
                if survey.longitude is not None
                else ""
            ),
        ]

        field_values = []

        for field in fields:
            answer_data = (
                answers_by_survey_and_field.get(
                    (
                        survey.id,
                        field.id,
                    )
                )
            )

            if answer_data is None:
                field_values.append("")
                continue

            answer, option = answer_data

            field_values.append(
                get_answer_export_value(
                    answer=answer,
                    option=option,
                )
            )

        writer.writerow(
            row + field_values
        )

    # --------------------------------------------------------
    # UTF-8 + BOM
    # --------------------------------------------------------

    csv_content = (
        "\ufeff"
        + output.getvalue()
    ).encode(
        "utf-8"
    )

    filename = (
        f"form_{form.id}"
        f"_version_{version.version_number}"
        ".csv"
    )

    return Response(
        content=csv_content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{filename}"'
            )
        },
    )


# ============================================================
# EXPORTACIÓN EXCEL XLSX
# ============================================================

@router.get(
    "/form-versions/{form_version_id}/xlsx",
    responses={
        200: {
            "description": (
                "Archivo Excel generado correctamente"
            )
        },
        401: {
            "description": (
                "Se requiere autenticación"
            )
        },
        403: {
            "description": (
                "Usuario sin acceso al proyecto"
            )
        },
        404: {
            "description": (
                "Versión o formulario no encontrado"
            )
        },
    },
)
def export_form_version_xlsx(
    form_version_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    (
        version,
        form,
        fields,
        survey_rows,
        answers_by_survey_and_field,
    ) = get_export_data(
        form_version_id=form_version_id,
        current_user=current_user,
        db=db,
    )

    workbook = Workbook()

    worksheet = workbook.worksheets[0]

    worksheet.title = "Encuestas"

    # --------------------------------------------------------
    # ENCABEZADOS
    # --------------------------------------------------------

    headers = [
        "survey_id",
        "uuid",
        "project_id",
        "form_id",
        "form_version_id",
        "version_number",
        "user_id",
        "employee_number",
        "status",
        "captured_at",
        "received_at",
        "latitude",
        "longitude",
    ]

    field_headers = [
        f"field_{field.id}_{field.name}"
        for field in fields
    ]

    worksheet.append(
        headers + field_headers
    )

    for cell in worksheet[1]:
        cell.font = Font(
            bold=True
        )

    # --------------------------------------------------------
    # FILAS
    # --------------------------------------------------------

    for survey, user in survey_rows:
        row = [
            survey.id,
            str(survey.uuid),
            form.project_id,
            form.id,
            version.id,
            version.version_number,
            user.id,
            user.employee_number,
            survey.status,
            survey.captured_at,
            survey.received_at,
            survey.latitude,
            survey.longitude,
        ]

        field_values = []

        for field in fields:
            answer_data = (
                answers_by_survey_and_field.get(
                    (
                        survey.id,
                        field.id,
                    )
                )
            )

            if answer_data is None:
                field_values.append(
                    None
                )
                continue

            answer, option = answer_data

            value = None

            # SELECT
            if (
                answer.field_option_id
                is not None
            ):
                if option is not None:
                    value = option.label
                else:
                    value = (
                        answer.field_option_id
                    )

            # TEXT / TEXTAREA
            elif (
                answer.value_text
                is not None
            ):
                value = answer.value_text

            # NUMBER
            elif (
                answer.value_number
                is not None
            ):
                value = float(
                    answer.value_number
                )

            # DATE
            elif (
                answer.value_date
                is not None
            ):
                value = answer.value_date

            # BOOLEAN
            elif (
                answer.value_boolean
                is not None
            ):
                value = answer.value_boolean

            field_values.append(
                value
            )

        worksheet.append(
            row + field_values
        )

    # --------------------------------------------------------
    # CONFIGURACIÓN VISUAL
    # --------------------------------------------------------

    worksheet.freeze_panes = "A2"

    worksheet.auto_filter.ref = (
        worksheet.dimensions
    )

    # --------------------------------------------------------
    # ANCHO DE COLUMNAS
    # --------------------------------------------------------

    for column_number in range(
        1,
        worksheet.max_column + 1,
    ):
        max_length = 0

        column_letter = (
            get_column_letter(
                column_number
            )
        )

        for row_number in range(
            1,
            worksheet.max_row + 1,
        ):
            cell = worksheet.cell(
                row=row_number,
                column=column_number,
            )

            if cell.value is None:
                continue

            value_length = len(
                str(cell.value)
            )

            if value_length > max_length:
                max_length = value_length

        worksheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 2,
            40,
        )

    # --------------------------------------------------------
    # FORMATO COORDENADAS
    # --------------------------------------------------------

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        worksheet.cell(
            row=row_number,
            column=12,
        ).number_format = (
            "0.000000"
        )

        worksheet.cell(
            row=row_number,
            column=13,
        ).number_format = (
            "0.000000"
        )

    # --------------------------------------------------------
    # FORMATO FECHAS
    # --------------------------------------------------------

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        worksheet.cell(
            row=row_number,
            column=10,
        ).number_format = (
            "yyyy-mm-dd hh:mm:ss"
        )

        worksheet.cell(
            row=row_number,
            column=11,
        ).number_format = (
            "yyyy-mm-dd hh:mm:ss"
        )

    # --------------------------------------------------------
    # GUARDAR XLSX EN MEMORIA
    # --------------------------------------------------------

    output = BytesIO()

    workbook.save(
        output
    )

    excel_content = (
        output.getvalue()
    )

    filename = (
        f"form_{form.id}"
        f"_version_{version.version_number}"
        ".xlsx"
    )

    return Response(
        content=excel_content,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{filename}"'
            )
        },
    )