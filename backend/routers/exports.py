import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Form,
    FormVersion,
    FormField,
    Survey,
    SurveyAnswer,
    FieldOption,
    User,
)


router = APIRouter(
    prefix="/exports",
    tags=["exports"],
)


def get_answer_export_value(
    answer: SurveyAnswer | None,
    option: FieldOption | None,
):
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
        return "true" if answer.value_boolean else "false"

    return ""


@router.get(
    "/form-versions/{form_version_id}/csv",
    responses={
        200: {
            "description": "Archivo CSV generado correctamente"
        },
        404: {
            "description": "Versión o formulario no encontrado"
        },
    },
)
def export_form_version_csv(
    form_version_id: int,
    db: Session = Depends(get_db),
):
    # 1. Verificar la versión
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

    # 2. Buscar el formulario
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

    # 3. Obtener los campos de la versión
    fields = db.scalars(
        select(FormField)
        .where(
            FormField.form_version_id == form_version_id
        )
        .order_by(
            FormField.field_order
        )
    ).all()

    # 4. Obtener encuestas y usuarios
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
            Survey.form_version_id == form_version_id,
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

    # 5. Cargar todas las respuestas de una sola vez
    answers_by_survey_and_field = {}

    if survey_ids:
        answer_rows = db.execute(
            select(
                SurveyAnswer,
                FieldOption,
            )
            .outerjoin(
                FieldOption,
                SurveyAnswer.field_option_id == FieldOption.id,
            )
            .where(
                SurveyAnswer.survey_id.in_(survey_ids)
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

    # 6. Crear CSV en memoria
    output = StringIO(newline="")

    writer = csv.writer(
        output,
        delimiter=";",
        lineterminator="\n",
    )

    # Columnas generales
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

    # Cada pregunta se convierte en una columna
    field_headers = [
        f"field_{field.id}_{field.name}"
        for field in fields
    ]

    writer.writerow(
        headers + field_headers
    )

    # 7. Crear una fila por encuesta
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
            str(survey.latitude).replace(".", ",")
            if survey.latitude is not None
            else ""
        ),
        (
            str(survey.longitude).replace(".", ",")
            if survey.longitude is not None
            else ""
        ),
        ]

        field_values = []

        for field in fields:
            answer_data = answers_by_survey_and_field.get(
                (
                    survey.id,
                    field.id,
                )
            )

            if answer_data is None:
                field_values.append("")
                continue

            answer, option = answer_data

            field_values.append(
                get_answer_export_value(
                    answer,
                    option,
                )
            )

        writer.writerow(
            row + field_values
        )

    # BOM UTF-8 para que Excel reconozca correctamente
    # caracteres como á, é, í, ó, ú y ñ.
    csv_content = (
        "\ufeff" + output.getvalue()
    ).encode("utf-8")

    filename = (
        f"form_{form.id}"
        f"_version_{version.version_number}"
        ".csv"
    )

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )