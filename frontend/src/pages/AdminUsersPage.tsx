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
  getProjects,
} from '../api/projects'

import {
  getRoles,
} from '../api/roles'

import {
  createUser,
  getUsers,
  resetUserPassword,
  updateUser,
} from '../api/users'

import {
  assignUserProject,
  getUserProjects,
  removeUserProject,
} from '../api/userProjects'

import type {
  AuthUser,
} from '../types/auth'

import type {
  Project,
} from '../types/project'

import type {
  Role,
} from '../types/role'

import type {
  User,
} from '../types/user'

import type {
  UserProject,
} from '../types/userProject'


const CONTROL_ROLES = new Set([
  'director',
  'jefe_nacional',
  'coordinador',
  'analista',
])


const PASSWORD_RESET_ROLES =
  new Set([
    'director',
    'jefe_nacional',
  ])


interface ApiError {
  detail?: string
}


interface UserFormState {
  employee_number: string
  identification: string
  password: string
  role_id: string
}


const EMPTY_FORM:
UserFormState = {
  employee_number: '',
  identification: '',
  password: '',
  role_id: '',
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


function formatRoleName(
  value: string,
): string {
  return value
    .replaceAll(
      '_',
      ' ',
    )
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    )
}


function AdminUsersPage() {
  const navigate =
    useNavigate()

  const [
    currentUser,
    setCurrentUser,
  ] =
    useState<AuthUser | null>(
      null,
    )

  const [
    users,
    setUsers,
  ] =
    useState<User[]>([])

  const [
    roles,
    setRoles,
  ] =
    useState<Role[]>([])

  const [
    projects,
    setProjects,
  ] =
    useState<Project[]>([])

  const [
    form,
    setForm,
  ] =
    useState<UserFormState>({
      ...EMPTY_FORM,
    })

  const [
    editingUserId,
    setEditingUserId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    assignmentUser,
    setAssignmentUser,
  ] =
    useState<User | null>(
      null,
    )

  const [
    assignments,
    setAssignments,
  ] =
    useState<UserProject[]>([])

  const [
    resetPasswordUser,
    setResetPasswordUser,
  ] =
    useState<User | null>(
      null,
    )

  const [
    newPassword,
    setNewPassword,
  ] =
    useState('')

  const [
    confirmPassword,
    setConfirmPassword,
  ] =
    useState('')

  const [
    isResettingPassword,
    setIsResettingPassword,
  ] =
    useState(false)

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
    isLoadingAssignments,
    setIsLoadingAssignments,
  ] =
    useState(false)

  const [
    assignmentProjectId,
    setAssignmentProjectId,
  ] =
    useState<number | null>(
      null,
    )

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

  const [
    assignmentError,
    setAssignmentError,
  ] =
    useState('')


  const canResetPasswords =
    currentUser !== null &&
    PASSWORD_RESET_ROLES.has(
      currentUser.role_name,
    )


  const loadUsers =
    async () => {
      const loadedUsers =
        await getUsers()

      setUsers(
        loadedUsers,
      )
    }


  const loadAssignments =
    async (
      userId: number,
    ) => {
      const loaded =
        await getUserProjects(
          userId,
        )

      setAssignments(
        loaded,
      )
    }


  useEffect(() => {
    const loadPage =
      async () => {
        try {
          const authenticatedUser =
            await getCurrentUser()

          if (
            !CONTROL_ROLES.has(
              authenticatedUser
                .role_name,
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

          setCurrentUser(
            authenticatedUser,
          )

          const [
            loadedUsers,
            loadedRoles,
            loadedProjects,
          ] =
            await Promise.all([
              getUsers(),
              getRoles(),
              getProjects(),
            ])

          setUsers(
            loadedUsers,
          )

          setRoles(
            loadedRoles,
          )

          setProjects(
            loadedProjects,
          )
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
            navigate(
              '/projects',
              {
                replace: true,
              },
            )

            return
          }

          setError(
            'No fue posible cargar la gestión de usuarios.',
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


  const getRoleName = (
    roleId: number,
  ): string => {
    const role =
      roles.find(
        (item) =>
          item.id ===
          roleId,
      )

    if (!role) {
      return (
        `Rol ${roleId}`
      )
    }

    return formatRoleName(
      role.name,
    )
  }


  const resetForm = () => {
    setEditingUserId(
      null,
    )

    setForm({
      ...EMPTY_FORM,
    })
  }


  const handleSubmit =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      setError('')
      setSuccess('')

      const username =
        form.employee_number
          .trim()

      const identification =
        form.identification
          .trim()

      const roleId =
        Number(
          form.role_id,
        )

      if (
        !username ||
        !identification ||
        !roleId
      ) {
        setError(
          'Usuario, identificación y rol son obligatorios.',
        )

        return
      }

      if (
        editingUserId ===
          null &&
        !form.password
      ) {
        setError(
          'La contraseña es obligatoria para crear un usuario.',
        )

        return
      }

      if (
        editingUserId ===
          null &&
        form.password.length <
          8
      ) {
        setError(
          'La contraseña debe tener al menos 8 caracteres.',
        )

        return
      }

      try {
        setIsSaving(
          true,
        )

        if (
          editingUserId ===
          null
        ) {
          await createUser({
            employee_number:
              username,

            identification,

            password:
              form.password,

            role_id:
              roleId,
          })

          setSuccess(
            'Usuario creado correctamente.',
          )
        } else {
          await updateUser(
            editingUserId,
            {
              employee_number:
                username,

              identification,

              role_id:
                roleId,
            },
          )

          setSuccess(
            'Usuario actualizado correctamente.',
          )
        }

        resetForm()

        await loadUsers()
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
          getApiErrorMessage(
            requestError,
            'No fue posible guardar el usuario.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const startEditing = (
    user: User,
  ) => {
    setError('')
    setSuccess('')

    setEditingUserId(
      user.id,
    )

    setForm({
      employee_number:
        user.employee_number,

      identification:
        user.identification,

      password: '',

      role_id:
        user.role_id
          .toString(),
    })

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }


  const handleToggleStatus =
    async (
      user: User,
    ) => {
      setError('')
      setSuccess('')

      if (
        user.id ===
        currentUser?.id
      ) {
        setError(
          'No puedes desactivar tu propio usuario.',
        )

        return
      }

      try {
        await updateUser(
          user.id,
          {
            is_active:
              !user.is_active,
          },
        )

        setSuccess(
          user.is_active
            ? 'Usuario desactivado correctamente.'
            : 'Usuario reactivado correctamente.',
        )

        await loadUsers()
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cambiar el estado del usuario.',
          ),
        )
      }
    }


  const openPasswordReset = (
    user: User,
  ) => {
    setError('')
    setSuccess('')

    setResetPasswordUser(
      user,
    )

    setNewPassword('')
    setConfirmPassword('')

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }


  const closePasswordReset = () => {
    setResetPasswordUser(
      null,
    )

    setNewPassword('')
    setConfirmPassword('')
  }


  const handlePasswordReset =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      setError('')
      setSuccess('')

      if (
        !resetPasswordUser
      ) {
        return
      }

      if (
        newPassword.length <
        8
      ) {
        setError(
          'La nueva contraseña debe tener al menos 8 caracteres.',
        )

        return
      }

      if (
        newPassword !==
        confirmPassword
      ) {
        setError(
          'Las contraseñas no coinciden.',
        )

        return
      }

      const confirmed =
        window.confirm(
          `¿Deseas restablecer la contraseña del usuario "${resetPasswordUser.employee_number}"?`,
        )

      if (!confirmed) {
        return
      }

      try {
        setIsResettingPassword(
          true,
        )

        await resetUserPassword(
          resetPasswordUser.id,
          newPassword,
        )

        setSuccess(
          `Contraseña de "${resetPasswordUser.employee_number}" restablecida correctamente.`,
        )

        closePasswordReset()
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
          getApiErrorMessage(
            requestError,
            'No fue posible restablecer la contraseña.',
          ),
        )
      } finally {
        setIsResettingPassword(
          false,
        )
      }
    }


  const openAssignments =
    async (
      user: User,
    ) => {
      setAssignmentError('')

      setAssignmentUser(
        user,
      )

      setIsLoadingAssignments(
        true,
      )

      try {
        await loadAssignments(
          user.id,
        )
      } catch (
        requestError
      ) {
        setAssignments([])

        setAssignmentError(
          getApiErrorMessage(
            requestError,
            'No fue posible consultar los proyectos del usuario.',
          ),
        )
      } finally {
        setIsLoadingAssignments(
          false,
        )
      }
    }


  const closeAssignments = () => {
    setAssignmentUser(
      null,
    )

    setAssignments([])

    setAssignmentError('')
  }


  const isAssigned = (
    projectId: number,
  ): boolean => {
    return assignments.some(
      (assignment) =>
        assignment.project_id ===
        projectId,
    )
  }


  const handleProjectAssignment =
    async (
      project: Project,
    ) => {
      if (!assignmentUser) {
        return
      }

      setAssignmentError('')
      setSuccess('')

      const alreadyAssigned =
        isAssigned(
          project.id,
        )

      if (
        alreadyAssigned &&
        assignmentUser.id ===
          currentUser?.id
      ) {
        setAssignmentError(
          'No puedes retirar desde aquí tu propia asignación a un proyecto.',
        )

        return
      }

      try {
        setAssignmentProjectId(
          project.id,
        )

        if (
          alreadyAssigned
        ) {
          await removeUserProject(
            assignmentUser.id,
            project.id,
          )

          setSuccess(
            'Usuario retirado del proyecto correctamente.',
          )
        } else {
          await assignUserProject({
            user_id:
              assignmentUser.id,

            project_id:
              project.id,
          })

          setSuccess(
            'Usuario asignado al proyecto correctamente.',
          )
        }

        await loadAssignments(
          assignmentUser.id,
        )
      } catch (
        requestError
      ) {
        setAssignmentError(
          getApiErrorMessage(
            requestError,
            'No fue posible modificar la asignación.',
          ),
        )
      } finally {
        setAssignmentProjectId(
          null,
        )
      }
    }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando gestión de
          usuarios...
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
            Administración de usuarios
          </p>
        </div>

        <div className="user-area">
          {currentUser && (
            <div>
              <strong>
                {
                  currentUser
                    .employee_number
                }
              </strong>

              <span>
                {
                  currentUser
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
                '/admin/projects',
              )
            }
          >
            Proyectos
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
            Volver
          </button>
        </div>
      </header>

      <section className="content-container">
        <div className="page-heading">
          <div>
            <h1>
              Gestión de usuarios
            </h1>

            <p>
              Crea, edita,
              activa, desactiva,
              asigna proyectos y
              administra accesos.
            </p>
          </div>
        </div>

        <div
          className="alert alert-offline"
          role="note"
        >
          Los usuarios no se
          eliminan del sistema.
          Cuando dejan de tener
          acceso se desactivan,
          conservando su historial.
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

        {resetPasswordUser && (
          <section className="admin-panel">
            <div className="page-heading">
              <div>
                <h2>
                  Restablecer contraseña
                </h2>

                <p>
                  Usuario:{' '}
                  <strong>
                    {
                      resetPasswordUser
                        .employee_number
                    }
                  </strong>
                </p>
              </div>

              <button
                type="button"
                className="outline-action"
                disabled={
                  isResettingPassword
                }
                onClick={
                  closePasswordReset
                }
              >
                Cerrar
              </button>
            </div>

            <div
              className="alert alert-offline"
              role="note"
            >
              La contraseña anterior
              no puede consultarse.
              Se asignará una nueva
              contraseña al usuario.
            </div>

            <form
              className="admin-form"
              onSubmit={
                handlePasswordReset
              }
            >
              <div className="admin-form-grid">
                <div className="form-field">
                  <label
                    htmlFor="new-password"
                  >
                    Nueva contraseña *
                  </label>

                  <input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    value={
                      newPassword
                    }
                    disabled={
                      isResettingPassword
                    }
                    onChange={(
                      event,
                    ) =>
                      setNewPassword(
                        event
                          .target
                          .value,
                      )
                    }
                  />
                </div>

                <div className="form-field">
                  <label
                    htmlFor="confirm-password"
                  >
                    Confirmar contraseña *
                  </label>

                  <input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    value={
                      confirmPassword
                    }
                    disabled={
                      isResettingPassword
                    }
                    onChange={(
                      event,
                    ) =>
                      setConfirmPassword(
                        event
                          .target
                          .value,
                      )
                    }
                  />
                </div>
              </div>

              <div className="admin-actions">
                <button
                  type="submit"
                  className="primary-action"
                  disabled={
                    isResettingPassword
                  }
                >
                  {isResettingPassword
                    ? 'Restableciendo...'
                    : 'Asignar nueva contraseña'}
                </button>

                <button
                  type="button"
                  className="outline-action"
                  disabled={
                    isResettingPassword
                  }
                  onClick={
                    closePasswordReset
                  }
                >
                  Cancelar
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="admin-panel">
          <h2>
            {editingUserId ===
            null
              ? 'Crear usuario'
              : 'Editar usuario'}
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
                  htmlFor="username"
                >
                  Usuario *
                </label>

                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  placeholder="Ej. CARLOS01"
                  value={
                    form.employee_number
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

                        employee_number:
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
                  htmlFor="identification"
                >
                  Identificación *
                </label>

                <input
                  id="identification"
                  type="text"
                  value={
                    form.identification
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

                        identification:
                          event
                            .target
                            .value,
                      }),
                    )
                  }
                />
              </div>

              {editingUserId ===
                null && (
                <div className="form-field">
                  <label
                    htmlFor="user-password"
                  >
                    Contraseña *
                  </label>

                  <input
                    id="user-password"
                    type="password"
                    autoComplete="new-password"
                    value={
                      form.password
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

                          password:
                            event
                              .target
                              .value,
                        }),
                      )
                    }
                  />
                </div>
              )}

              <div className="form-field">
                <label
                  htmlFor="user-role"
                >
                  Rol *
                </label>

                <select
                  id="user-role"
                  value={
                    form.role_id
                  }
                  disabled={
                    isSaving ||
                    editingUserId ===
                      currentUser?.id
                  }
                  onChange={(
                    event,
                  ) =>
                    setForm(
                      (
                        current,
                      ) => ({
                        ...current,

                        role_id:
                          event
                            .target
                            .value,
                      }),
                    )
                  }
                >
                  <option value="">
                    Seleccione un rol
                  </option>

                  {roles.map(
                    (role) => (
                      <option
                        key={
                          role.id
                        }
                        value={
                          role.id
                        }
                      >
                        {
                          formatRoleName(
                            role.name,
                          )
                        }
                      </option>
                    ),
                  )}
                </select>
              </div>
            </div>

            {editingUserId ===
              currentUser?.id && (
              <div
                className="alert alert-offline"
                role="note"
              >
                Por seguridad no
                puedes cambiar tu
                propio rol.
              </div>
            )}

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
                  : editingUserId ===
                    null
                    ? 'Crear usuario'
                    : 'Guardar cambios'}
              </button>

              {editingUserId !==
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

        {assignmentUser && (
          <section className="admin-panel">
            <div className="page-heading">
              <div>
                <h2>
                  Proyectos de{' '}
                  {
                    assignmentUser
                      .employee_number
                  }
                </h2>

                <p>
                  Asigna o retira
                  proyectos disponibles
                  para este usuario.
                </p>
              </div>

              <button
                type="button"
                className="outline-action"
                onClick={
                  closeAssignments
                }
              >
                Cerrar
              </button>
            </div>

            {assignmentError && (
              <div
                className="alert alert-error"
                role="alert"
              >
                {assignmentError}
              </div>
            )}

            {isLoadingAssignments ? (
              <p>
                Cargando proyectos...
              </p>
            ) : (
              <>
                {projects.length ===
                  0 && (
                  <div className="empty-state">
                    <h2>
                      Sin proyectos
                    </h2>

                    <p>
                      No tienes proyectos
                      disponibles para
                      administrar.
                    </p>
                  </div>
                )}

                <div className="project-grid">
                  {projects.map(
                    (project) => {
                      const assigned =
                        isAssigned(
                          project.id,
                        )

                      const isOwnUser =
                        assignmentUser.id ===
                        currentUser?.id

                      return (
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
                                assigned
                                  ? 'status status-active'
                                  : 'status status-inactive'
                              }
                            >
                              {assigned
                                ? 'Asignado'
                                : 'No asignado'}
                            </span>
                          </div>

                          <p>
                            {
                              project
                                .description ??
                              'Sin descripción.'
                            }
                          </p>

                          <button
                            type="button"
                            className={
                              assigned
                                ? 'outline-action'
                                : 'primary-action'
                            }
                            disabled={
                              assignmentProjectId ===
                                project.id ||
                              (
                                assigned &&
                                isOwnUser
                              )
                            }
                            onClick={() =>
                              void handleProjectAssignment(
                                project,
                              )
                            }
                          >
                            {assignmentProjectId ===
                            project.id
                              ? 'Procesando...'
                              : assigned
                                ? isOwnUser
                                  ? 'Asignación propia'
                                  : 'Retirar del proyecto'
                                : 'Asignar al proyecto'}
                          </button>
                        </article>
                      )
                    },
                  )}
                </div>
              </>
            )}
          </section>
        )}

        <section className="admin-list-section">
          <div className="page-heading">
            <div>
              <h2>
                Usuarios registrados
              </h2>

              <p>
                {users.length}
                {' '}
                {users.length ===
                1
                  ? 'usuario'
                  : 'usuarios'}
              </p>
            </div>
          </div>

          <div className="project-grid">
            {users.map(
              (user) => {
                const isCurrentUser =
                  user.id ===
                  currentUser?.id

                return (
                  <article
                    className="project-card"
                    key={
                      user.id
                    }
                  >
                    <div className="card-heading">
                      <h2>
                        {
                          user
                            .employee_number
                        }
                      </h2>

                      <span
                        className={
                          user.is_active
                            ? 'status status-active'
                            : 'status status-inactive'
                        }
                      >
                        {user.is_active
                          ? 'Activo'
                          : 'Inactivo'}
                      </span>
                    </div>

                    <p>
                      <strong>
                        Identificación:
                      </strong>{' '}
                      {
                        user
                          .identification
                      }
                    </p>

                    <p>
                      <strong>
                        Rol:
                      </strong>{' '}
                      {
                        getRoleName(
                          user.role_id,
                        )
                      }
                    </p>

                    {isCurrentUser && (
                      <p>
                        <strong>
                          Usuario actual
                        </strong>
                      </p>
                    )}

                    <div className="admin-card-actions">
                      <button
                        type="button"
                        className="primary-action"
                        onClick={() =>
                          startEditing(
                            user,
                          )
                        }
                      >
                        Editar
                      </button>

                      <button
                        type="button"
                        className="outline-action"
                        disabled={
                          isCurrentUser
                        }
                        onClick={() =>
                          void handleToggleStatus(
                            user,
                          )
                        }
                      >
                        {isCurrentUser
                          ? 'Usuario actual'
                          : user.is_active
                            ? 'Desactivar'
                            : 'Reactivar'}
                      </button>

                      <button
                        type="button"
                        className="outline-action"
                        onClick={() =>
                          void openAssignments(
                            user,
                          )
                        }
                      >
                        Proyectos
                      </button>

                      {canResetPasswords &&
                        !isCurrentUser && (
                        <button
                          type="button"
                          className="outline-action"
                          onClick={() =>
                            openPasswordReset(
                              user,
                            )
                          }
                        >
                          Restablecer contraseña
                        </button>
                      )}
                    </div>
                  </article>
                )
              },
            )}
          </div>
        </section>
      </section>
    </main>
  )
}


export default AdminUsersPage