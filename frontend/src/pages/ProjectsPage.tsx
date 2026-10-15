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
} from '../api/auth'

import api from '../api/client'

import type {
  AuthUser,
} from '../types/auth'

import type {
  Project,
} from '../types/project'


function ProjectsPage() {
  const navigate = useNavigate()

  const [user, setUser] =
    useState<AuthUser | null>(null)

  const [projects, setProjects] =
    useState<Project[]>([])

  const [isLoading, setIsLoading] =
    useState(true)

  const [error, setError] =
    useState('')


  useEffect(() => {
    const loadPage = async () => {
      try {
        const [
          currentUser,
          projectsResponse,
        ] = await Promise.all([
          getCurrentUser(),
          api.get<Project[]>(
            '/projects',
          ),
        ])

        setUser(currentUser)
        setProjects(
          projectsResponse.data,
        )
      } catch (requestError) {
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

        setError(
          'No fue posible cargar los proyectos.',
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadPage()
  }, [navigate])


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
                {user.employee_number}
              </strong>

              <span>
                {user.role_name}
              </span>
            </div>
          )}

          <button
            className="secondary-button"
            type="button"
            onClick={handleLogout}
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <section className="content-container">
        <div className="page-heading">
          <div>
            <h1>
              Mis proyectos
            </h1>

            <p>
              Selecciona un proyecto
              para continuar.
            </p>
          </div>
        </div>

        {error && (
          <div
            className="alert alert-error"
          >
            {error}
          </div>
        )}

        {!error &&
          projects.length === 0 && (
            <div className="empty-state">
              <h2>
                Sin proyectos asignados
              </h2>

              <p>
                No tienes proyectos
                asociados actualmente.
              </p>
            </div>
          )}

        <div className="project-grid">
          {projects.map(
            (project) => (
              <article
                className="project-card"
                key={project.id}
              >
                <div className="card-heading">
                  <h2>
                    {project.name}
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
                  {project.description ??
                    'Sin descripción.'}
                </p>

                <button
                  type="button"
                  disabled={
                    project.status !==
                    'active'
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