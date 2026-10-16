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
} from '../api/auth'

import {
  getSurveyDetail,
} from '../api/surveys'

import type {
  SurveyDetailAnswer,
  SurveyDetailResponse,
} from '../types/surveyDetail'


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
          const data =
            await getSurveyDetail(
              numericSurveyId,
            )

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

                      {answer.was_corrected && (
                        <p>
                          <strong>
                            Correcciones:
                          </strong>{' '}
                          {
                            answer.correction_count
                          }
                        </p>
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