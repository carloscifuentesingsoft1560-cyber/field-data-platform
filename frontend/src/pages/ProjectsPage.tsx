import {
  useEffect,
  useState,
} from 'react'

import axios from 'axios'

import {
  useNavigate,
} from 'react-router-dom'

import {
  clearSession,
  getCurrentUser,
  getSessionUserId,
} from '../api/auth'

import api from '../api/client'

import {
  cacheProjects,
  cacheUser,
  getCachedProjects,
  getCachedUser,
} from '../services/offlineCache'

import type {
  AuthUser,
} from '../types/auth'

import type {
  Project,
} from '../types/project'


const CONTROL_ROLES = new Set([
  'director',
  'jefe_nacional',
  'coordinador',
  'analista',
])


function ProjectsPage() {
  const navigate =
    useNavigate()

  const [
    user,
    setUser,
  ] =
    useState<AuthUser | null>(
      null,
    )

  const [
    projects,
    setProjects,
  ] =
    useState<Project[]>([])

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


  useEffect(() => {
    const loadPage =
      async () => {
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
            currentUser,
            projectsResponse,
          ] =
            await Promise.all([
              getCurrentUser(),

              api.get<Project[]>(
                '/projects',
              ),
            ])

          setUser(
            currentUser,
          )

          setProjects(
            projectsResponse.data,
          )

          setIsOfflineData(
            false,
          )

          /*
           * El fallo del caché local no
           * debe impedir el uso online.
           */
          try {
            await Promise.all([
              cacheUser(
                currentUser,
              ),

              cacheProjects(
                currentUser.id,
                projectsResponse.data,
              ),
            ])
          } catch {
            // La API ya respondió.
          }
        } catch (
          requestError
        ) {
          if (
            axios.isAxiosError(
              requestError,
            ) &&
            requestError.response
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

          /*
           * Si no fue un 401,
           * intentamos trabajar
           * completamente desde
           * IndexedDB.
           */
          try {
            const [
              cachedUser,
              cachedProjects,
            ] =
              await Promise.all([
                getCachedUser(
                  ownerUserId,
                ),

                getCachedProjects(
                  ownerUserId,
                ),
              ])

            if (
              !cachedUser &&
              cachedProjects.length ===
                0
            ) {
              setError(
                'No fue posible cargar los proyectos y no hay información disponible sin conexión.',
              )

              return
            }

            setUser(
              cachedUser,
            )

            setProjects(
              cachedProjects,
            )

            setIsOfflineData(
              true,
            )
          } catch {
            setError(
              'No fue posible cargar los proyectos.',
            )
          }
        } finally {
          setIsLoading(
            false,
          )
        }
      }

    void loadPage()
  }, [
    navigate,
  ])


  const handleLogout = () => {
    clearSession()

    navigate(
      '/login',
      {
        replace: true,
      },
    )
  }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando información...
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
            Gestión de proyectos
            asignados
          </p>
        </div>

        <div className="user-area">
          {user && (
            <div>
              <strong>
                {
                  user
                    .employee_number
                }
              </strong>

              <span>
                {
                  user
                    .role_name
                }
              </span>
            </div>
          )}

          {user &&
            CONTROL_ROLES.has(
              user.role_name,
            ) && (
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  navigate(
                    '/admin/projects',
                  )
                }
              >
                Administrar
              </button>
            )}

          <button
            className="secondary-button"
            type="button"
            onClick={
              handleLogout
            }
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <section className="content-container">
        {isOfflineData && (
          <div
            className="alert alert-offline"
            role="status"
          >
            Modo sin conexión:
            mostrando información
            guardada en este
            dispositivo.
          </div>
        )}

        <div className="page-heading">
          <div>
            <h1>
              Mis proyectos
            </h1>

            <p>
              Selecciona un
              proyecto para
              continuar.
            </p>
          </div>

          <span className="project-count">
            {projects.length}
            {' '}
            {projects.length ===
            1
              ? 'proyecto'
              : 'proyectos'}
          </span>
        </div>

        {error && (
          <div
            className="alert alert-error"
            role="alert"
          >
            {error}
          </div>
        )}

        {!error &&
          projects.length ===
            0 && (
            <div className="empty-state">
              <h2>
                Sin proyectos
                asignados
              </h2>

              <p>
                Actualmente no
                tienes proyectos
                asociados a tu
                usuario.
              </p>
            </div>
          )}

        <div className="project-grid">
          {projects.map(
            (project) => (
              <article
                className="project-card"
                key={
                  project.id
                }
              >
                <div className="card-heading">
                  <h2>
                    {
                      project
                        .name
                    }
                  </h2>

                  <span
                    className={
                      project.status ===
                      'active'
                        ? 'status status-active'
                        : 'status status-inactive'
                    }
                  >
                    {project.status ===
                    'active'
                      ? 'Activo'
                      : 'Inactivo'}
                  </span>
                </div>

                <p>
                  {project
                    .description ??
                    'Sin descripción.'}
                </p>

                <div className="project-dates">
                  <span>
                    Inicio:{' '}
                    {
                      project
                        .start_date
                    }
                  </span>

                  {project.end_date && (
                    <span>
                      Finalización:{' '}
                      {
                        project
                          .end_date
                      }
                    </span>
                  )}
                </div>

                <button
                  type="button"
                  disabled={
                    project.status !==
                    'active'
                  }
                  onClick={() =>
                    navigate(
                      `/projects/${project.id}`,
                    )
                  }
                >
                  Abrir proyecto
                </button>
              </article>
            ),
          )}
        </div>
      </section>
    </main>
  )
}


export default ProjectsPage