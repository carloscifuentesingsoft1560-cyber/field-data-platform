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
  getSessionUserId,
} from '../api/auth'

import api from '../api/client'

import {
  cacheForms,
  cacheUser,
  getCachedFormsByProject,
  getCachedProject,
  getCachedUser,
} from '../services/offlineCache'

import type {
  AuthUser,
} from '../types/auth'

import type {
  Form,
} from '../types/form'

import type {
  Project,
} from '../types/project'


const CONTROL_ROLES = new Set([
  'director',
  'jefe_nacional',
  'coordinador',
  'analista',
])


function ProjectFormsPage() {
  const navigate =
    useNavigate()

  const {
    projectId,
  } =
    useParams()

  const [
    currentUser,
    setCurrentUser,
  ] =
    useState<AuthUser | null>(
      null,
    )

  const [
    project,
    setProject,
  ] =
    useState<Project | null>(
      null,
    )

  const [
    forms,
    setForms,
  ] =
    useState<Form[]>([])

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
    isOfflineData,
    setIsOfflineData,
  ] =
    useState(false)


  const canManageForms =
    currentUser !== null &&
    CONTROL_ROLES.has(
      currentUser.role_name,
    )


  useEffect(() => {
    const loadData =
      async () => {
        const numericProjectId =
          Number(
            projectId,
          )

        if (
          !projectId ||
          Number.isNaN(
            numericProjectId,
          )
        ) {
          setError(
            'El proyecto seleccionado no es válido.',
          )

          setIsLoading(
            false,
          )

          return
        }

        const ownerUserId =
          getSessionUserId()

        if (!ownerUserId) {
          clearSession()

          navigate(
            '/login',
            {
              replace: true,
            },
          )

          return
        }

        try {
          const [
            authenticatedUser,
            projectResponse,
            formsResponse,
          ] =
            await Promise.all([
              getCurrentUser(),

              api.get<Project>(
                `/projects/${numericProjectId}`,
              ),

              api.get<Form[]>(
                '/forms/',
              ),
            ])

          const projectForms =
            formsResponse.data.filter(
              (form) =>
                form.project_id ===
                numericProjectId,
            )

          setCurrentUser(
            authenticatedUser,
          )

          setProject(
            projectResponse.data,
          )

          setForms(
            projectForms,
          )

          setIsOfflineData(
            false,
          )

          try {
            await Promise.all([
              cacheUser(
                authenticatedUser,
              ),

              cacheForms(
                ownerUserId,
                formsResponse.data,
              ),
            ])
          } catch {
            /*
             * Un problema con IndexedDB
             * no debe impedir el uso
             * normal cuando la API está
             * disponible.
             */
          }
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

            if (
              status === 401
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

            if (
              status === 403 ||
              status === 404
            ) {
              setError(
                'No tienes acceso a este proyecto o el proyecto no existe.',
              )

              return
            }
          }

          /*
           * Si no hay conexión,
           * intentamos recuperar
           * proyecto, formularios y
           * usuario desde IndexedDB.
           */
          try {
            const [
              cachedUser,
              cachedProject,
              cachedForms,
            ] =
              await Promise.all([
                getCachedUser(
                  ownerUserId,
                ),

                getCachedProject(
                  ownerUserId,
                  numericProjectId,
                ),

                getCachedFormsByProject(
                  ownerUserId,
                  numericProjectId,
                ),
              ])

            if (!cachedProject) {
              setError(
                'No fue posible cargar este proyecto y no está disponible sin conexión.',
              )

              return
            }

            setCurrentUser(
              cachedUser,
            )

            setProject(
              cachedProject,
            )

            setForms(
              cachedForms,
            )

            setIsOfflineData(
              true,
            )
          } catch {
            setError(
              'No fue posible cargar los formularios.',
            )
          }
        } finally {
          setIsLoading(
            false,
          )
        }
      }

    void loadData()
  }, [
    navigate,
    projectId,
  ])


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando formularios...
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
            Formularios del proyecto
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() =>
            navigate(
              '/projects',
            )
          }
        >
          Volver a proyectos
        </button>
      </header>

      <section className="content-container">
        {isOfflineData && (
          <div
            className="alert alert-offline"
            role="status"
          >
            Modo sin conexión:
            mostrando formularios
            guardados en este
            dispositivo.
          </div>
        )}

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
                    {
                      project.name
                    }
                  </h1>

                  <p>
                    Selecciona un formulario
                    para diligenciar una
                    encuesta o administra
                    los formularios del
                    proyecto.
                  </p>
                </div>

                <div className="admin-actions">
                  {canManageForms &&
                    !isOfflineData && (
                      <button
                        type="button"
                        className="primary-action"
                        onClick={() =>
                          navigate(
                            `/admin/projects/${project.id}/forms`,
                          )
                        }
                      >
                        Administrar formularios
                      </button>
                    )}

                  <button
                    type="button"
                    className="outline-action"
                    onClick={() =>
                      navigate(
                        `/projects/${project.id}/surveys`,
                      )
                    }
                  >
                    Ver encuestas
                  </button>
                </div>
              </div>

              {forms.length ===
                0 && (
                <div className="empty-state">
                  <h2>
                    Sin formularios
                  </h2>

                  {canManageForms &&
                  !isOfflineData ? (
                    <>
                      <p>
                        Este proyecto todavía
                        no tiene formularios.
                        Crea el primero para
                        comenzar a capturar
                        encuestas.
                      </p>

                      <div
                        className="admin-actions"
                        style={{
                          justifyContent:
                            'center',
                          marginTop:
                            '20px',
                        }}
                      >
                        <button
                          type="button"
                          className="primary-action"
                          onClick={() =>
                            navigate(
                              `/admin/projects/${project.id}/forms`,
                            )
                          }
                        >
                          Crear formulario
                        </button>
                      </div>
                    </>
                  ) : (
                    <p>
                      Este proyecto no tiene
                      formularios disponibles.
                    </p>
                  )}
                </div>
              )}

              <div className="project-grid">
                {forms.map(
                  (form) => (
                    <article
                      className="project-card"
                      key={
                        form.id
                      }
                    >
                      <div className="card-heading">
                        <h2>
                          {
                            form.name
                          }
                        </h2>

                        <span
                          className={
                            form.is_active
                              ? 'status status-active'
                              : 'status status-inactive'
                          }
                        >
                          {form.is_active
                            ? 'Activo'
                            : 'Inactivo'}
                        </span>
                      </div>

                      <p>
                        {form.description ??
                          'Sin descripción.'}
                      </p>

                      <button
                        type="button"
                        disabled={
                          !form.is_active
                        }
                        onClick={() =>
                          navigate(
                            `/projects/${project.id}/forms/${form.id}`,
                          )
                        }
                      >
                        Diligenciar encuesta
                      </button>
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


export default ProjectFormsPage