import {
  type FormEvent,
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

import {
  createProject,
  deleteProject,
  getProjects,
  updateProject,
} from '../api/projects'

import type {
  AuthUser,
} from '../types/auth'

import type {
  Project,
  ProjectStatus,
} from '../types/project'


const CONTROL_ROLES = new Set([
  'director',
  'jefe_nacional',
  'coordinador',
  'analista',
])


interface ApiError {
  detail?: string
}


interface ProjectFormState {
  name: string
  description: string
  status: ProjectStatus
  start_date: string
  end_date: string
}


const EMPTY_FORM:
ProjectFormState = {
  name: '',
  description: '',
  status: 'active',
  start_date: '',
  end_date: '',
}


function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (
    axios.isAxiosError<ApiError>(
      error,
    )
  ) {
    const detail =
      error.response
        ?.data
        ?.detail

    if (
      typeof detail ===
      'string'
    ) {
      return detail
    }
  }

  return fallback
}


function AdminProjectsPage() {
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
    form,
    setForm,
  ] =
    useState<ProjectFormState>(
      EMPTY_FORM,
    )

  const [
    editingProjectId,
    setEditingProjectId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    isLoading,
    setIsLoading,
  ] =
    useState(true)

  const [
    isSaving,
    setIsSaving,
  ] =
    useState(false)

  const [
    error,
    setError,
  ] =
    useState('')

  const [
    success,
    setSuccess,
  ] =
    useState('')


  const loadProjects =
    async () => {
      const loadedProjects =
        await getProjects()

      setProjects(
        loadedProjects,
      )
    }


  useEffect(() => {
    const loadPage =
      async () => {
        try {
          const currentUser =
            await getCurrentUser()

          if (
            !CONTROL_ROLES.has(
              currentUser.role_name,
            )
          ) {
            navigate(
              '/projects',
              {
                replace: true,
              },
            )

            return
          }

          setUser(
            currentUser,
          )

          await loadProjects()
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

          setError(
            'No fue posible cargar la administración de proyectos.',
          )
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


  const resetForm = () => {
    setForm({
      ...EMPTY_FORM,
    })

    setEditingProjectId(
      null,
    )
  }


  const handleSubmit =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      setError('')
      setSuccess('')

      if (
        !form.name.trim() ||
        !form.start_date
      ) {
        setError(
          'El nombre y la fecha de inicio son obligatorios.',
        )

        return
      }

      if (
        form.end_date &&
        form.end_date <
          form.start_date
      ) {
        setError(
          'La fecha de finalización no puede ser anterior a la fecha de inicio.',
        )

        return
      }

      const payload = {
        name:
          form.name.trim(),

        description:
          form.description
            .trim() || null,

        status:
          form.status,

        start_date:
          form.start_date,

        end_date:
          form.end_date ||
          null,
      }

      try {
        setIsSaving(
          true,
        )

        if (
          editingProjectId ===
          null
        ) {
          await createProject(
            payload,
          )

          setSuccess(
            'Proyecto creado correctamente.',
          )
        } else {
          await updateProject(
            editingProjectId,
            payload,
          )

          setSuccess(
            'Proyecto actualizado correctamente.',
          )
        }

        resetForm()

        await loadProjects()
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

        if (
          axios.isAxiosError(
            requestError,
          ) &&
          requestError.response
            ?.status === 403
        ) {
          setError(
            'No tienes permisos para realizar esta operación.',
          )

          return
        }

        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible guardar el proyecto.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const startEditing = (
    project: Project,
  ) => {
    setError('')
    setSuccess('')

    setEditingProjectId(
      project.id,
    )

    setForm({
      name:
        project.name,

      description:
        project.description ??
        '',

      status:
        project.status,

      start_date:
        project.start_date,

      end_date:
        project.end_date ??
        '',
    })

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }


  const handleToggleStatus =
    async (
      project: Project,
    ) => {
      setError('')
      setSuccess('')

      const newStatus:
      ProjectStatus =
        project.status ===
        'active'
          ? 'inactive'
          : 'active'

      try {
        await updateProject(
          project.id,
          {
            status:
              newStatus,
          },
        )

        setSuccess(
          newStatus ===
          'active'
            ? 'Proyecto activado correctamente.'
            : 'Proyecto inactivado correctamente.',
        )

        await loadProjects()
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cambiar el estado del proyecto.',
          ),
        )
      }
    }


  const handleDelete =
    async (
      project: Project,
    ) => {
      const confirmed =
        window.confirm(
          `¿Deseas eliminar el proyecto "${project.name}"? Esta acción solo será permitida si el proyecto no tiene formularios asociados.`,
        )

      if (!confirmed) {
        return
      }

      setError('')
      setSuccess('')

      try {
        await deleteProject(
          project.id,
        )

        setSuccess(
          'Proyecto eliminado correctamente.',
        )

        if (
          editingProjectId ===
          project.id
        ) {
          resetForm()
        }

        await loadProjects()
      } catch (
        requestError
      ) {
        if (
          axios.isAxiosError(
            requestError,
          ) &&
          requestError.response
            ?.status === 409
        ) {
          setError(
            getApiErrorMessage(
              requestError,
              'El proyecto tiene información asociada y no puede eliminarse.',
            ),
          )

          return
        }

        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible eliminar el proyecto.',
          ),
        )
      }
    }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando administración...
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
            Administración de proyectos
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

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              navigate(
                '/admin/users',
              )
            }
          >
            Usuarios
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              navigate(
                '/projects',
              )
            }
          >
            Volver a proyectos
          </button>
        </div>
      </header>

      <section className="content-container">
        <div className="page-heading">
          <div>
            <h1>
              Gestión de proyectos
            </h1>

            <p>
              Crea, edita y administra
              los proyectos disponibles.
            </p>
          </div>
        </div>

        {error && (
          <div
            className="alert alert-error"
            role="alert"
          >
            {error}
          </div>
        )}

        {success && (
          <div
            className="alert alert-success"
            role="status"
          >
            {success}
          </div>
        )}

        <section className="admin-panel">
          <h2>
            {editingProjectId ===
            null
              ? 'Crear proyecto'
              : 'Editar proyecto'}
          </h2>

          <form
            className="admin-form"
            onSubmit={
              handleSubmit
            }
          >
            <div className="admin-form-grid">
              <div className="form-field">
                <label
                  htmlFor="project-name"
                >
                  Nombre *
                </label>

                <input
                  id="project-name"
                  type="text"
                  value={
                    form.name
                  }
                  disabled={
                    isSaving
                  }
                  onChange={(
                    event,
                  ) =>
                    setForm(
                      (
                        current,
                      ) => ({
                        ...current,
                        name:
                          event
                            .target
                            .value,
                      }),
                    )
                  }
                />
              </div>

              <div className="form-field">
                <label
                  htmlFor="project-status"
                >
                  Estado
                </label>

                <select
                  id="project-status"
                  value={
                    form.status
                  }
                  disabled={
                    isSaving
                  }
                  onChange={(
                    event,
                  ) =>
                    setForm(
                      (
                        current,
                      ) => ({
                        ...current,
                        status:
                          event
                            .target
                            .value as ProjectStatus,
                      }),
                    )
                  }
                >
                  <option value="active">
                    Activo
                  </option>

                  <option value="inactive">
                    Inactivo
                  </option>
                </select>
              </div>

              <div className="form-field">
                <label
                  htmlFor="project-start-date"
                >
                  Fecha de inicio *
                </label>

                <input
                  id="project-start-date"
                  type="date"
                  value={
                    form.start_date
                  }
                  disabled={
                    isSaving
                  }
                  onChange={(
                    event,
                  ) =>
                    setForm(
                      (
                        current,
                      ) => ({
                        ...current,
                        start_date:
                          event
                            .target
                            .value,
                      }),
                    )
                  }
                />
              </div>

              <div className="form-field">
                <label
                  htmlFor="project-end-date"
                >
                  Fecha de finalización
                </label>

                <input
                  id="project-end-date"
                  type="date"
                  value={
                    form.end_date
                  }
                  disabled={
                    isSaving
                  }
                  onChange={(
                    event,
                  ) =>
                    setForm(
                      (
                        current,
                      ) => ({
                        ...current,
                        end_date:
                          event
                            .target
                            .value,
                      }),
                    )
                  }
                />
              </div>
            </div>

            <div className="form-field">
              <label
                htmlFor="project-description"
              >
                Descripción
              </label>

              <textarea
                id="project-description"
                value={
                  form.description
                }
                disabled={
                  isSaving
                }
                onChange={(
                  event,
                ) =>
                  setForm(
                    (
                      current,
                    ) => ({
                      ...current,
                      description:
                        event
                          .target
                          .value,
                    }),
                  )
                }
              />
            </div>

            <div className="admin-actions">
              <button
                type="submit"
                className="primary-action"
                disabled={
                  isSaving
                }
              >
                {isSaving
                  ? 'Guardando...'
                  : editingProjectId ===
                    null
                    ? 'Crear proyecto'
                    : 'Guardar cambios'}
              </button>

              {editingProjectId !==
                null && (
                <button
                  type="button"
                  className="outline-action"
                  disabled={
                    isSaving
                  }
                  onClick={
                    resetForm
                  }
                >
                  Cancelar edición
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="admin-list-section">
          <div className="page-heading">
            <div>
              <h2>
                Proyectos administrados
              </h2>

              <p>
                {projects.length}
                {' '}
                {projects.length ===
                1
                  ? 'proyecto disponible'
                  : 'proyectos disponibles'}
              </p>
            </div>
          </div>

          {projects.length ===
            0 && (
            <div className="empty-state">
              <h2>
                Sin proyectos
              </h2>

              <p>
                Crea el primer proyecto
                utilizando el formulario
                superior.
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
                        project.name
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
                    {project.description ??
                      'Sin descripción.'}
                  </p>

                  <div className="project-dates">
                    <span>
                      Inicio:{' '}
                      {
                        project.start_date
                      }
                    </span>

                    {project.end_date && (
                      <span>
                        Finalización:{' '}
                        {
                          project.end_date
                        }
                      </span>
                    )}
                  </div>

                  <div className="admin-card-actions">
                    <button
                      type="button"
                      className="primary-action"
                      onClick={() =>
                        startEditing(
                          project,
                        )
                      }
                    >
                      Editar
                    </button>

                    <button
                      type="button"
                      className="outline-action"
                      onClick={() =>
                        void handleToggleStatus(
                          project,
                        )
                      }
                    >
                      {project.status ===
                      'active'
                        ? 'Inactivar'
                        : 'Activar'}
                    </button>

                    <button
                      type="button"
                      className="danger-action"
                      onClick={() =>
                        void handleDelete(
                          project,
                        )
                      }
                    >
                      Eliminar
                    </button>
                  </div>
                </article>
              ),
            )}
          </div>
        </section>
      </section>
    </main>
  )
}


export default AdminProjectsPage