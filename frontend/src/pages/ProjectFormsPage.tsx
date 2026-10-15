import {
  useEffect,
  useState,
} from 'react'

import axios from 'axios'
import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import api from '../api/client'

import {
  clearSession,
} from '../api/auth'

import type {
  Form,
} from '../types/form'

import type {
  Project,
} from '../types/project'


function ProjectFormsPage() {
  const navigate = useNavigate()
  const { projectId } = useParams()

  const [project, setProject] =
    useState<Project | null>(null)

  const [forms, setForms] =
    useState<Form[]>([])

  const [isLoading, setIsLoading] =
    useState(true)

  const [error, setError] =
    useState('')


  useEffect(() => {
    const loadData = async () => {
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
        ] = await Promise.all([
          api.get<Project>(
            `/projects/${numericProjectId}`,
          ),
          api.get<Form[]>(
            '/forms/',
          ),
        ])

        setProject(
          projectResponse.data,
        )

        setForms(
          formsResponse.data.filter(
            (form) =>
              form.project_id ===
              numericProjectId,
          ),
        )
      } catch (requestError) {
        if (
          axios.isAxiosError(
            requestError,
          )
        ) {
          const status =
            requestError.response
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

        setError(
          'No fue posible cargar los formularios.',
        )
      } finally {
        setIsLoading(false)
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
            navigate('/projects')
          }
        >
          Volver a proyectos
        </button>
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
                    {project.name}
                  </h1>

                  <p>
                    Selecciona un
                    formulario para
                    continuar.
                  </p>
                </div>
              </div>

              {forms.length === 0 && (
                <div className="empty-state">
                  <h2>
                    Sin formularios
                  </h2>

                  <p>
                    Este proyecto no tiene
                    formularios disponibles.
                  </p>
                </div>
              )}

              <div className="project-grid">
                {forms.map(
                  (form) => (
                    <article
                      className="project-card"
                      key={form.id}
                    >
                      <div className="card-heading">
                        <h2>
                          {form.name}
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
                      >
                        Abrir formulario
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