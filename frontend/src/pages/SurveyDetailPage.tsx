import {
  useEffect,
  useState,
} from 'react'

import axios from 'axios'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import {
  clearSession,
  getCurrentUser,
} from '../api/auth'

import api from '../api/client'

import {
  correctSurveyAnswer,
} from '../api/surveyAnswers'

import {
  getSurveyDetail,
} from '../api/surveys'

import type {
  FieldOption,
} from '../types/fieldOption'

import type {
  SurveyAnswerCorrection,
  SurveyAnswerUpdatePayload,
} from '../types/surveyAnswer'

import type {
  SurveyDetailAnswer,
  SurveyDetailResponse,
} from '../types/surveyDetail'


const CONTROL_ROLES =
  new Set([
    'director',
    'jefe_nacional',
    'coordinador',
    'analista',
  ])


function normalizeRoleName(
  value: string,
): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_')
}


function formatDateTime(
  value: string,
): string {
  const date =
    new Date(value)

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value
  }

  return new Intl.DateTimeFormat(
    'es-CO',
    {
      dateStyle: 'medium',
      timeStyle: 'short',
    },
  ).format(date)
}


function formatDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T00:00:00`,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value
  }

  return new Intl.DateTimeFormat(
    'es-CO',
    {
      dateStyle: 'medium',
    },
  ).format(date)
}


function formatAnswer(
  answer: SurveyDetailAnswer,
): string {
  if (!answer.answered) {
    return 'Sin respuesta'
  }

  if (
    answer.field_type ===
    'select'
  ) {
    return (
      answer.option_label ??
      answer.option_value ??
      'Sin respuesta'
    )
  }

  if (
    answer.field_type ===
    'boolean'
  ) {
    if (
      answer.value_boolean ===
      true
    ) {
      return 'Sí'
    }

    if (
      answer.value_boolean ===
      false
    ) {
      return 'No'
    }

    return 'Sin respuesta'
  }

  if (
    answer.field_type ===
    'number'
  ) {
    return answer.value_number !==
      null
      ? String(
          answer.value_number,
        )
      : 'Sin respuesta'
  }

  if (
    answer.field_type ===
    'date'
  ) {
    return answer.value_date
      ? formatDate(
          answer.value_date,
        )
      : 'Sin respuesta'
  }

  return (
    answer.value_text ??
    'Sin respuesta'
  )
}


function getInitialCorrectionValue(
  answer: SurveyDetailAnswer,
): string {
  if (
    answer.field_type ===
    'select'
  ) {
    return answer.field_option_id !==
      null
      ? String(
          answer.field_option_id,
        )
      : ''
  }

  if (
    answer.field_type ===
    'boolean'
  ) {
    if (
      answer.value_boolean ===
      true
    ) {
      return 'true'
    }

    if (
      answer.value_boolean ===
      false
    ) {
      return 'false'
    }

    return ''
  }

  if (
    answer.field_type ===
    'number'
  ) {
    return answer.value_number !==
      null
      ? String(
          answer.value_number,
        )
      : ''
  }

  if (
    answer.field_type ===
    'date'
  ) {
    return (
      answer.value_date ??
      ''
    )
  }

  return (
    answer.value_text ??
    ''
  )
}


function formatBooleanValue(
  value: boolean | null,
): string {
  if (value === true) {
    return 'Sí'
  }

  if (value === false) {
    return 'No'
  }

  return 'Sin valor'
}


function formatCorrectionValue(
  answer: SurveyDetailAnswer,
  correction: SurveyAnswerCorrection,
  valueType: 'old' | 'new',
): string {
  if (
    answer.field_type ===
      'text' ||
    answer.field_type ===
      'textarea'
  ) {
    const value =
      valueType === 'old'
        ? correction.old_value_text
        : correction.new_value_text

    return (
      value ??
      'Sin valor'
    )
  }

  if (
    answer.field_type ===
    'number'
  ) {
    const value =
      valueType === 'old'
        ? correction.old_value_number
        : correction.new_value_number

    return value !== null
      ? String(value)
      : 'Sin valor'
  }

  if (
    answer.field_type ===
    'date'
  ) {
    const value =
      valueType === 'old'
        ? correction.old_value_date
        : correction.new_value_date

    return value
      ? formatDate(value)
      : 'Sin valor'
  }

  if (
    answer.field_type ===
    'boolean'
  ) {
    const value =
      valueType === 'old'
        ? correction.old_value_boolean
        : correction.new_value_boolean

    return formatBooleanValue(
      value,
    )
  }

  if (
    answer.field_type ===
    'select'
  ) {
    const optionId =
      valueType === 'old'
        ? correction.old_field_option_id
        : correction.new_field_option_id

    if (
      optionId === null
    ) {
      return 'Sin valor'
    }

    if (
      valueType === 'new' &&
      optionId ===
        answer.field_option_id &&
      answer.option_label
    ) {
      return answer.option_label
    }

    return `Opción #${optionId}`
  }

  return 'Sin valor'
}


function SurveyDetailPage() {
  const navigate =
    useNavigate()

  const {
    projectId,
    surveyId,
  } =
    useParams()

  const [
    survey,
    setSurvey,
  ] =
    useState<
      SurveyDetailResponse | null
    >(null)

  const [
    isLoading,
    setIsLoading,
  ] =
    useState(true)

  const [
    error,
    setError,
  ] =
    useState('')

  const [
    canCorrect,
    setCanCorrect,
  ] =
    useState(false)

  const [
    editingAnswerId,
    setEditingAnswerId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    expandedHistoryAnswerId,
    setExpandedHistoryAnswerId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    correctionValue,
    setCorrectionValue,
  ] =
    useState('')

  const [
    correctionReason,
    setCorrectionReason,
  ] =
    useState('')

  const [
    correctionError,
    setCorrectionError,
  ] =
    useState('')

  const [
    correctionSuccess,
    setCorrectionSuccess,
  ] =
    useState('')

  const [
    fieldOptions,
    setFieldOptions,
  ] =
    useState<FieldOption[]>(
      [],
    )

  const [
    isLoadingOptions,
    setIsLoadingOptions,
  ] =
    useState(false)

  const [
    isSavingCorrection,
    setIsSavingCorrection,
  ] =
    useState(false)


  useEffect(() => {
    const loadSurvey =
      async () => {
        const numericProjectId =
          Number(projectId)

        const numericSurveyId =
          Number(surveyId)

        if (
          !projectId ||
          !surveyId ||
          Number.isNaN(
            numericProjectId,
          ) ||
          Number.isNaN(
            numericSurveyId,
          )
        ) {
          setError(
            'La encuesta seleccionada no es válida.',
          )

          setIsLoading(false)

          return
        }

        try {
          const [
            data,
            currentUser,
          ] =
            await Promise.all([
              getSurveyDetail(
                numericSurveyId,
              ),

              getCurrentUser(),
            ])

          if (
            data.project_id !==
            numericProjectId
          ) {
            setError(
              'La encuesta no pertenece al proyecto seleccionado.',
            )

            return
          }

          setSurvey(data)

          setCanCorrect(
            CONTROL_ROLES.has(
              normalizeRoleName(
                currentUser.role_name,
              ),
            ),
          )
        } catch (
          requestError
        ) {
          if (
            axios.isAxiosError(
              requestError,
            )
          ) {
            const status =
              requestError
                .response
                ?.status

            if (status === 401) {
              clearSession()

              navigate(
                '/login',
                {
                  replace: true,
                },
              )

              return
            }

            if (status === 403) {
              setError(
                'No tienes acceso a esta encuesta.',
              )

              return
            }

            if (status === 404) {
              setError(
                'La encuesta no existe.',
              )

              return
            }
          }

          setError(
            'No fue posible cargar el detalle de la encuesta.',
          )
        } finally {
          setIsLoading(false)
        }
      }

    void loadSurvey()
  }, [
    navigate,
    projectId,
    surveyId,
  ])


  const startCorrection =
    async (
      answer:
        SurveyDetailAnswer,
    ) => {
      if (
        answer.answer_id ===
        null
      ) {
        return
      }

      setEditingAnswerId(
        answer.answer_id,
      )

      setExpandedHistoryAnswerId(
        null,
      )

      setCorrectionValue(
        getInitialCorrectionValue(
          answer,
        ),
      )

      setCorrectionReason('')

      setCorrectionError('')

      setCorrectionSuccess('')

      setFieldOptions([])

      if (
        answer.field_type !==
        'select'
      ) {
        return
      }

      setIsLoadingOptions(true)

      try {
        const response =
          await api.get<
            FieldOption[]
          >(
            `/field-options/by-field/${answer.form_field_id}`,
          )

        setFieldOptions(
          response.data,
        )
      } catch (
        requestError
      ) {
        if (
          axios.isAxiosError(
            requestError,
          ) &&
          requestError
            .response
            ?.status === 401
        ) {
          clearSession()

          navigate(
            '/login',
            {
              replace: true,
            },
          )

          return
        }

        setCorrectionError(
          'No fue posible cargar las opciones de este campo.',
        )
      } finally {
        setIsLoadingOptions(
          false,
        )
      }
    }


  const cancelCorrection =
    () => {
      setEditingAnswerId(
        null,
      )

      setCorrectionValue('')

      setCorrectionReason('')

      setCorrectionError('')

      setFieldOptions([])
    }


  const toggleHistory =
    (
      answerId: number,
    ) => {
      setEditingAnswerId(
        null,
      )

      setCorrectionError('')

      setExpandedHistoryAnswerId(
        (
          currentAnswerId,
        ) =>
          currentAnswerId ===
          answerId
            ? null
            : answerId,
      )
    }


  const saveCorrection =
    async (
      answer:
        SurveyDetailAnswer,
    ) => {
      if (
        answer.answer_id ===
        null
      ) {
        return
      }

      const reason =
        correctionReason.trim()

      if (!reason) {
        setCorrectionError(
          'Debes indicar el motivo de la corrección.',
        )

        return
      }

      const payload:
        SurveyAnswerUpdatePayload =
        {
          reason,
        }

      if (
        answer.field_type ===
          'text' ||
        answer.field_type ===
          'textarea'
      ) {
        if (
          !correctionValue.trim()
        ) {
          setCorrectionError(
            'Debes ingresar el nuevo valor.',
          )

          return
        }

        payload.value_text =
          correctionValue
      } else if (
        answer.field_type ===
        'number'
      ) {
        if (
          !correctionValue.trim()
        ) {
          setCorrectionError(
            'Debes ingresar un número.',
          )

          return
        }

        const numericValue =
          Number(
            correctionValue,
          )

        if (
          !Number.isFinite(
            numericValue,
          )
        ) {
          setCorrectionError(
            'El nuevo valor debe ser un número válido.',
          )

          return
        }

        payload.value_number =
          numericValue
      } else if (
        answer.field_type ===
        'date'
      ) {
        if (!correctionValue) {
          setCorrectionError(
            'Debes seleccionar una fecha.',
          )

          return
        }

        payload.value_date =
          correctionValue
      } else if (
        answer.field_type ===
        'boolean'
      ) {
        if (
          correctionValue !==
            'true' &&
          correctionValue !==
            'false'
        ) {
          setCorrectionError(
            'Debes seleccionar Sí o No.',
          )

          return
        }

        payload.value_boolean =
          correctionValue ===
          'true'
      } else if (
        answer.field_type ===
        'select'
      ) {
        const optionId =
          Number(
            correctionValue,
          )

        if (
          !correctionValue ||
          Number.isNaN(
            optionId,
          )
        ) {
          setCorrectionError(
            'Debes seleccionar una opción.',
          )

          return
        }

        payload.field_option_id =
          optionId
      } else {
        setCorrectionError(
          'Este tipo de campo no admite corrección desde la interfaz.',
        )

        return
      }

      setIsSavingCorrection(
        true,
      )

      setCorrectionError('')

      setCorrectionSuccess('')

      try {
        await correctSurveyAnswer(
          answer.answer_id,
          payload,
        )

        const numericSurveyId =
          Number(surveyId)

        const refreshedSurvey =
          await getSurveyDetail(
            numericSurveyId,
          )

        setSurvey(
          refreshedSurvey,
        )

        setEditingAnswerId(
          null,
        )

        setExpandedHistoryAnswerId(
          answer.answer_id,
        )

        setCorrectionValue('')

        setCorrectionReason('')

        setFieldOptions([])

        setCorrectionSuccess(
          `La respuesta "${answer.field_name}" fue corregida correctamente.`,
        )
      } catch (
        requestError
      ) {
        if (
          axios.isAxiosError(
            requestError,
          )
        ) {
          const status =
            requestError
              .response
              ?.status

          if (status === 401) {
            clearSession()

            navigate(
              '/login',
              {
                replace: true,
              },
            )

            return
          }

          if (status === 403) {
            setCorrectionError(
              'Tu usuario no tiene autorización para corregir esta respuesta.',
            )

            return
          }

          const responseData =
            requestError
              .response
              ?.data as
              | {
                  detail?: string
                }
              | undefined

          if (
            responseData?.detail
          ) {
            setCorrectionError(
              responseData.detail,
            )

            return
          }
        }

        setCorrectionError(
          'No fue posible guardar la corrección.',
        )
      } finally {
        setIsSavingCorrection(
          false,
        )
      }
    }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando encuesta...
        </p>
      </main>
    )
  }


  return (
    <main className="projects-page">
      <header className="app-header">
        <div>
          <span className="app-name">
            Field Data Platform
          </span>

          <p>
            Revisión de encuesta
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              navigate(
                '/projects',
              )
            }
          >
            Ver proyectos
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              navigate(
                `/projects/${projectId}/surveys`,
              )
            }
          >
            Volver a encuestas
          </button>
        </div>
      </header>

      <section className="content-container">
        {error && (
          <div
            className="alert alert-error"
            role="alert"
          >
            {error}
          </div>
        )}

        {correctionSuccess && (
          <div
            className="alert alert-success"
            role="status"
          >
            {correctionSuccess}
          </div>
        )}

        {!error &&
          survey && (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    Encuesta #
                    {survey.id}
                  </h1>

                  <p>
                    {survey.form_name}
                    {' · '}
                    Versión{' '}
                    {
                      survey.version_number
                    }
                  </p>
                </div>
              </div>

              <article className="project-card">
                <div className="card-heading">
                  <h2>
                    Información general
                  </h2>

                  <span
                    className={
                      survey.status ===
                      'submitted'
                        ? 'status status-active'
                        : 'status status-inactive'
                    }
                  >
                    {survey.status}
                  </span>
                </div>

                <p>
                  <strong>
                    Empleado:
                  </strong>{' '}
                  {
                    survey.employee_number
                  }
                </p>

                <p>
                  <strong>
                    Capturada:
                  </strong>{' '}
                  {formatDateTime(
                    survey.captured_at,
                  )}
                </p>

                <p>
                  <strong>
                    Recibida:
                  </strong>{' '}
                  {formatDateTime(
                    survey.received_at,
                  )}
                </p>

                {survey.latitude !==
                  null &&
                  survey.longitude !==
                    null && (
                    <p>
                      <strong>
                        Ubicación:
                      </strong>{' '}
                      {survey.latitude},
                      {' '}
                      {survey.longitude}
                    </p>
                  )}
              </article>

              <div
                className="page-heading"
                style={{
                  marginTop:
                    '36px',
                }}
              >
                <div>
                  <h1>
                    Respuestas
                  </h1>

                  <p>
                    {
                      survey.answers.length
                    }{' '}
                    campos del formulario
                  </p>
                </div>
              </div>

              <div className="project-grid">
                {survey.answers.map(
                  (answer) => (
                    <article
                      className="project-card"
                      key={
                        answer.form_field_id
                      }
                    >
                      <div className="card-heading">
                        <h2>
                          {
                            answer.field_order
                          }
                          .{' '}
                          {
                            answer.field_name
                          }
                        </h2>

                        <span
                          className={
                            answer.answered
                              ? 'status status-active'
                              : 'status status-inactive'
                          }
                        >
                          {answer.answered
                            ? 'Respondida'
                            : 'Sin respuesta'}
                        </span>
                      </div>

                      <p>
                        <strong>
                          Respuesta:
                        </strong>{' '}
                        {formatAnswer(
                          answer,
                        )}
                      </p>

                      <p>
                        <strong>
                          Tipo:
                        </strong>{' '}
                        {
                          answer.field_type
                        }
                      </p>

                      <p>
                        <strong>
                          Obligatoria:
                        </strong>{' '}
                        {answer.is_required
                          ? 'Sí'
                          : 'No'}
                      </p>

                      {answer.was_corrected &&
                        answer.answer_id !==
                          null && (
                          <>
                            <p>
                              <strong>
                                Correcciones:
                              </strong>{' '}
                              {
                                answer.correction_count
                              }
                            </p>

                            <button
                              type="button"
                              className="outline-action"
                              onClick={() =>
                                toggleHistory(
                                  answer.answer_id as number,
                                )
                              }
                            >
                              {expandedHistoryAnswerId ===
                              answer.answer_id
                                ? 'Ocultar historial'
                                : 'Ver historial'}
                            </button>
                          </>
                        )}

                      {expandedHistoryAnswerId ===
                        answer.answer_id &&
                        answer.corrections.length >
                          0 && (
                          <div className="correction-history">
                            <h3>
                              Historial de correcciones
                            </h3>

                            {[...answer.corrections]
                              .reverse()
                              .map(
                                (
                                  correction,
                                  index,
                                ) => (
                                  <div
                                    className="correction-history-item"
                                    key={
                                      correction.id
                                    }
                                  >
                                    <div className="correction-history-heading">
                                      <strong>
                                        Corrección{' '}
                                        {
                                          answer
                                            .correction_count -
                                          index
                                        }
                                      </strong>

                                      <span>
                                        {formatDateTime(
                                          correction.corrected_at,
                                        )}
                                      </span>
                                    </div>

                                    <p>
                                      <strong>
                                        Valor anterior:
                                      </strong>{' '}
                                      {formatCorrectionValue(
                                        answer,
                                        correction,
                                        'old',
                                      )}
                                    </p>

                                    <p>
                                      <strong>
                                        Valor nuevo:
                                      </strong>{' '}
                                      {formatCorrectionValue(
                                        answer,
                                        correction,
                                        'new',
                                      )}
                                    </p>

                                    <p>
                                      <strong>
                                        Motivo:
                                      </strong>{' '}
                                      {correction.reason ??
                                        'Sin motivo registrado'}
                                    </p>

                                    <p>
                                      <strong>
                                        Corregido por usuario:
                                      </strong>{' '}
                                      {
                                        correction.corrected_by_user_id
                                      }
                                    </p>
                                  </div>
                                ),
                              )}
                          </div>
                        )}

                      {canCorrect &&
                        survey.status ===
                          'submitted' &&
                        answer.answered &&
                        answer.answer_id !==
                          null && (
                          <>
                            {editingAnswerId ===
                            answer.answer_id ? (
                              <div className="correction-panel">
                                <h3>
                                  Corregir respuesta
                                </h3>

                                <div className="form-field">
                                  <label>
                                    Nuevo valor *
                                  </label>

                                  {answer.field_type ===
                                    'text' && (
                                    <input
                                      type="text"
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    />
                                  )}

                                  {answer.field_type ===
                                    'textarea' && (
                                    <textarea
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    />
                                  )}

                                  {answer.field_type ===
                                    'number' && (
                                    <input
                                      type="number"
                                      step="any"
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    />
                                  )}

                                  {answer.field_type ===
                                    'date' && (
                                    <input
                                      type="date"
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    />
                                  )}

                                  {answer.field_type ===
                                    'boolean' && (
                                    <select
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    >
                                      <option value="">
                                        Seleccione
                                      </option>

                                      <option value="true">
                                        Sí
                                      </option>

                                      <option value="false">
                                        No
                                      </option>
                                    </select>
                                  )}

                                  {answer.field_type ===
                                    'select' && (
                                    <select
                                      value={
                                        correctionValue
                                      }
                                      disabled={
                                        isSavingCorrection ||
                                        isLoadingOptions
                                      }
                                      onChange={(
                                        event,
                                      ) =>
                                        setCorrectionValue(
                                          event
                                            .target
                                            .value,
                                        )
                                      }
                                    >
                                      <option value="">
                                        {isLoadingOptions
                                          ? 'Cargando opciones...'
                                          : 'Seleccione una opción'}
                                      </option>

                                      {fieldOptions.map(
                                        (
                                          option,
                                        ) => (
                                          <option
                                            key={
                                              option.id
                                            }
                                            value={
                                              option.id
                                            }
                                          >
                                            {
                                              option.label
                                            }
                                          </option>
                                        ),
                                      )}
                                    </select>
                                  )}
                                </div>

                                <div className="form-field">
                                  <label>
                                    Motivo de la corrección *
                                  </label>

                                  <textarea
                                    value={
                                      correctionReason
                                    }
                                    disabled={
                                      isSavingCorrection
                                    }
                                    placeholder="Explica por qué debe modificarse esta respuesta."
                                    onChange={(
                                      event,
                                    ) =>
                                      setCorrectionReason(
                                        event
                                          .target
                                          .value,
                                      )
                                    }
                                  />
                                </div>

                                {correctionError && (
                                  <div
                                    className="alert alert-error"
                                    role="alert"
                                  >
                                    {
                                      correctionError
                                    }
                                  </div>
                                )}

                                <div className="correction-actions">
                                  <button
                                    type="button"
                                    className="primary-action"
                                    disabled={
                                      isSavingCorrection ||
                                      isLoadingOptions
                                    }
                                    onClick={() =>
                                      void saveCorrection(
                                        answer,
                                      )
                                    }
                                  >
                                    {isSavingCorrection
                                      ? 'Guardando...'
                                      : 'Guardar corrección'}
                                  </button>

                                  <button
                                    type="button"
                                    className="outline-action"
                                    disabled={
                                      isSavingCorrection
                                    }
                                    onClick={
                                      cancelCorrection
                                    }
                                  >
                                    Cancelar
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <button
                                type="button"
                                className="primary-action"
                                onClick={() =>
                                  void startCorrection(
                                    answer,
                                  )
                                }
                              >
                                Corregir respuesta
                              </button>
                            )}
                          </>
                        )}
                    </article>
                  ),
                )}
              </div>
            </>
          )}
      </section>
    </main>
  )
}


export default SurveyDetailPage