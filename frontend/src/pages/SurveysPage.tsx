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

import api from '../api/client'

import {
  getSurveys,
} from '../api/surveys'

import type {
  Form,
} from '../types/form'

import type {
  FormVersion,
} from '../types/formVersion'

import type {
  Project,
} from '../types/project'

import type {
  SurveyRecord,
} from '../types/survey'


interface SurveyListItem {
  survey: SurveyRecord
  formName: string
  versionNumber: number
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


function SurveysPage() {
  const navigate =
    useNavigate()

  const { projectId } =
    useParams()

  const [
    project,
    setProject,
  ] =
    useState<Project | null>(
      null,
    )

  const [
    surveys,
    setSurveys,
  ] =
    useState<SurveyListItem[]>(
      [],
    )

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
    const loadSurveys =
      async () => {
        const numericProjectId =
          Number(projectId)

        if (
          !projectId ||
          Number.isNaN(
            numericProjectId,
          )
        ) {
          setError(
            'El proyecto seleccionado no es válido.',
          )

          setIsLoading(false)

          return
        }

        try {
          const [
            projectResponse,
            formsResponse,
            surveyRecords,
          ] =
            await Promise.all([
              api.get<Project>(
                `/projects/${numericProjectId}`,
              ),

              api.get<Form[]>(
                '/forms/',
              ),

              getSurveys(),
            ])

          const projectForms =
            formsResponse.data.filter(
              (form) =>
                form.project_id ===
                numericProjectId,
            )

          const versionsByForm =
            await Promise.all(
              projectForms.map(
                async (form) => {
                  const response =
                    await api.get<
                      FormVersion[]
                    >(
                      `/form-versions/form/${form.id}`,
                    )

                  return {
                    form,
                    versions:
                      response.data,
                  }
                },
              ),
            )

          const versionMap =
            new Map<
              number,
              {
                formName: string
                versionNumber: number
              }
            >()

          versionsByForm.forEach(
            ({
              form,
              versions,
            }) => {
              versions.forEach(
                (version) => {
                  versionMap.set(
                    version.id,
                    {
                      formName:
                        form.name,

                      versionNumber:
                        version.version_number,
                    },
                  )
                },
              )
            },
          )

          const projectSurveys =
            surveyRecords
              .filter(
                (survey) =>
                  versionMap.has(
                    survey.form_version_id,
                  ),
              )
              .map(
                (survey) => {
                  const versionInfo =
                    versionMap.get(
                      survey.form_version_id,
                    )

                  return {
                    survey,

                    formName:
                      versionInfo?.formName ??
                      'Formulario',

                    versionNumber:
                      versionInfo
                        ?.versionNumber ??
                      0,
                  }
                },
              )

          setProject(
            projectResponse.data,
          )

          setSurveys(
            projectSurveys,
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
                'No tienes acceso a las encuestas de este proyecto.',
              )

              return
            }

            if (status === 404) {
              setError(
                'El proyecto solicitado no existe.',
              )

              return
            }
          }

          setError(
            'No fue posible cargar las encuestas. Verifica la conexión con el servidor.',
          )
        } finally {
          setIsLoading(false)
        }
      }

    void loadSurveys()
  }, [
    navigate,
    projectId,
  ])


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando encuestas...
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
            Encuestas recibidas
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
                `/projects/${projectId}`,
              )
            }
          >
            Volver al proyecto
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
          project && (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    Encuestas
                  </h1>

                  <p>
                    {project.name}
                  </p>
                </div>
              </div>

              {surveys.length ===
                0 ? (
                <div className="empty-state">
                  <h2>
                    Sin encuestas
                  </h2>

                  <p>
                    Todavía no hay
                    encuestas recibidas
                    para este proyecto.
                  </p>
                </div>
              ) : (
                <div className="project-grid">
                  {surveys.map(
                    ({
                      survey,
                      formName,
                      versionNumber,
                    }) => (
                      <article
                        className="project-card"
                        key={
                          survey.id
                        }
                      >
                        <div className="card-heading">
                          <h2>
                            Encuesta #
                            {survey.id}
                          </h2>

                          <span
                            className={
                              survey.status ===
                              'submitted'
                                ? 'status status-active'
                                : 'status status-inactive'
                            }
                          >
                            {
                              survey.status
                            }
                          </span>
                        </div>

                        <p>
                          <strong>
                            Formulario:
                          </strong>{' '}
                          {formName}
                        </p>

                        <p>
                          <strong>
                            Versión:
                          </strong>{' '}
                          {versionNumber}
                        </p>

                        <p>
                          <strong>
                            Usuario:
                          </strong>{' '}
                          {survey.user_id}
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
                              {
                                survey.latitude
                              }
                              ,{' '}
                              {
                                survey.longitude
                              }
                            </p>
                          )}

                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/projects/${project.id}/surveys/${survey.id}`,
                            )
                          }
                        >
                          Abrir encuesta
                        </button>
                      </article>
                    ),
                  )}
                </div>
              )}
            </>
          )}
      </section>
    </main>
  )
}


export default SurveysPage