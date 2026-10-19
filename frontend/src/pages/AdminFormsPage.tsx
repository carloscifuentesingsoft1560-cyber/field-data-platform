import {
  type FormEvent,
  useEffect,
  useMemo,
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

import {
  createFieldOption,
  deleteFieldOption,
  getFieldOptions,
  updateFieldOption,
} from '../api/fieldOptions'

import {
  createFormField,
  deleteFormField,
  getFormFields,
  reorderFormField,
  updateFormField,
} from '../api/formFields'

import {
  createFormVersion,
  getFormVersions,
  publishFormVersion,
} from '../api/formVersions'

import {
  createForm,
  getForms,
  updateForm,
} from '../api/forms'

import api from '../api/client'

import type {
  AuthUser,
} from '../types/auth'

import type {
  FieldOption,
} from '../types/fieldOption'

import type {
  Form,
} from '../types/form'

import type {
  FormField,
  FormFieldType,
} from '../types/formField'

import type {
  FormVersion,
} from '../types/formVersion'

import type {
  Project,
} from '../types/project'


const CONTROL_ROLES = new Set([
  'director',
  'jefe_nacional',
  'coordinador',
  'analista',
])


const FIELD_TYPE_LABELS:
Record<FormFieldType, string> = {
  text: 'Texto corto',
  textarea: 'Texto largo',
  number: 'Número',
  date: 'Fecha',
  boolean: 'Sí / No',
  select: 'Lista de opciones',
}


interface ApiError {
  detail?: string
}


interface FormEditorState {
  name: string
  description: string
}


interface FieldEditorState {
  name: string
  field_type: FormFieldType
  is_required: boolean
}


interface OptionEditorState {
  label: string
  value: string
}


const EMPTY_FORM:
FormEditorState = {
  name: '',
  description: '',
}


const EMPTY_FIELD:
FieldEditorState = {
  name: '',
  field_type: 'text',
  is_required: false,
}


const EMPTY_OPTION:
OptionEditorState = {
  label: '',
  value: '',
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


function AdminFormsPage() {
  const navigate =
    useNavigate()

  const {
    projectId,
  } =
    useParams()

  const numericProjectId =
    Number(
      projectId,
    )

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
    formEditor,
    setFormEditor,
  ] =
    useState<FormEditorState>(
      EMPTY_FORM,
    )

  const [
    editingFormId,
    setEditingFormId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    selectedFormId,
    setSelectedFormId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    versions,
    setVersions,
  ] =
    useState<FormVersion[]>([])

  const [
    selectedVersionId,
    setSelectedVersionId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    fields,
    setFields,
  ] =
    useState<FormField[]>([])

  const [
    fieldEditor,
    setFieldEditor,
  ] =
    useState<FieldEditorState>(
      EMPTY_FIELD,
    )

  const [
    editingFieldId,
    setEditingFieldId,
  ] =
    useState<number | null>(
      null,
    )

  const [
    optionField,
    setOptionField,
  ] =
    useState<FormField | null>(
      null,
    )

  const [
    options,
    setOptions,
  ] =
    useState<FieldOption[]>([])

  const [
    optionEditor,
    setOptionEditor,
  ] =
    useState<OptionEditorState>(
      EMPTY_OPTION,
    )

  const [
    editingOptionId,
    setEditingOptionId,
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


  const selectedForm =
    useMemo(
      () =>
        forms.find(
          (form) =>
            form.id ===
            selectedFormId,
        ) ??
        null,
      [
        forms,
        selectedFormId,
      ],
    )


  const selectedVersion =
    useMemo(
      () =>
        versions.find(
          (version) =>
            version.id ===
            selectedVersionId,
        ) ??
        null,
      [
        versions,
        selectedVersionId,
      ],
    )


  const hasDraft =
    versions.some(
      (version) =>
        version.status ===
        'draft',
    )


  const loadForms =
    async () => {
      const loadedForms =
        await getForms()

      setForms(
        loadedForms.filter(
          (form) =>
            form.project_id ===
            numericProjectId,
        ),
      )
    }


  const loadFields =
    async (
      versionId: number,
    ) => {
      const loadedFields =
        await getFormFields(
          versionId,
        )

      setFields(
        loadedFields,
      )
    }


  const loadVersions =
    async (
      formId: number,
    ) => {
      const loadedVersions =
        await getFormVersions(
          formId,
        )

      setVersions(
        loadedVersions,
      )

      const draft =
        [...loadedVersions]
          .reverse()
          .find(
            (version) =>
              version.status ===
              'draft',
          )

      const published =
        [...loadedVersions]
          .reverse()
          .find(
            (version) =>
              version.status ===
              'published',
          )

      const versionToSelect =
        draft ??
        published ??
        loadedVersions[
          loadedVersions.length - 1
        ] ??
        null

      if (
        versionToSelect
      ) {
        setSelectedVersionId(
          versionToSelect.id,
        )

        await loadFields(
          versionToSelect.id,
        )
      } else {
        setSelectedVersionId(
          null,
        )

        setFields(
          [],
        )
      }
    }


  useEffect(() => {
    const loadPage =
      async () => {
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

        try {
          const [
            authenticatedUser,
            projectResponse,
            loadedForms,
          ] =
            await Promise.all([
              getCurrentUser(),

              api.get<Project>(
                `/projects/${numericProjectId}`,
              ),

              getForms(),
            ])

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

          setProject(
            projectResponse.data,
          )

          setForms(
            loadedForms.filter(
              (form) =>
                form.project_id ===
                numericProjectId,
            ),
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

          setError(
            getApiErrorMessage(
              requestError,
              'No fue posible cargar la administración de formularios.',
            ),
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
    numericProjectId,
    projectId,
  ])


  const resetFormEditor =
    () => {
      setFormEditor({
        ...EMPTY_FORM,
      })

      setEditingFormId(
        null,
      )
    }


  const resetFieldEditor =
    () => {
      setFieldEditor({
        ...EMPTY_FIELD,
      })

      setEditingFieldId(
        null,
      )
    }


  const resetOptionEditor =
    () => {
      setOptionEditor({
        ...EMPTY_OPTION,
      })

      setEditingOptionId(
        null,
      )
    }


  const handleFormSubmit =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      setError('')
      setSuccess('')

      const name =
        formEditor.name.trim()

      if (!name) {
        setError(
          'El nombre del formulario es obligatorio.',
        )

        return
      }

      try {
        setIsSaving(
          true,
        )

        if (
          editingFormId ===
          null
        ) {
          const newForm =
            await createForm({
              project_id:
                numericProjectId,

              name,

              description:
                formEditor
                  .description
                  .trim() ||
                null,
            })

          setSuccess(
            'Formulario creado correctamente.',
          )

          resetFormEditor()

          await loadForms()

          setSelectedFormId(
            newForm.id,
          )

          await loadVersions(
            newForm.id,
          )
        } else {
          await updateForm(
            editingFormId,
            {
              name,

              description:
                formEditor
                  .description
                  .trim() ||
                null,
            },
          )

          setSuccess(
            'Formulario actualizado correctamente.',
          )

          resetFormEditor()

          await loadForms()
        }
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible guardar el formulario.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const startEditingForm =
    (
      form: Form,
    ) => {
      setError('')
      setSuccess('')

      setEditingFormId(
        form.id,
      )

      setFormEditor({
        name:
          form.name,

        description:
          form.description ??
          '',
      })

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      })
    }


  const toggleFormStatus =
    async (
      form: Form,
    ) => {
      setError('')
      setSuccess('')

      try {
        await updateForm(
          form.id,
          {
            is_active:
              !form.is_active,
          },
        )

        setSuccess(
          form.is_active
            ? 'Formulario inactivado correctamente.'
            : 'Formulario activado correctamente.',
        )

        await loadForms()
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cambiar el estado del formulario.',
          ),
        )
      }
    }


  const openBuilder =
    async (
      form: Form,
    ) => {
      setError('')
      setSuccess('')

      setSelectedFormId(
        form.id,
      )

      setOptionField(
        null,
      )

      resetFieldEditor()
      resetOptionEditor()

      try {
        await loadVersions(
          form.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cargar las versiones del formulario.',
          ),
        )
      }
    }


  const createDraftVersion =
    async () => {
      if (!selectedForm) {
        return
      }

      setError('')
      setSuccess('')

      if (hasDraft) {
        setError(
          'Ya existe una versión en borrador. Debes terminarla o publicarla antes de crear otra.',
        )

        return
      }

      try {
        setIsSaving(
          true,
        )

        const version =
          await createFormVersion({
            form_id:
              selectedForm.id,
          })

        setSuccess(
          `Versión ${version.version_number} creada en borrador.`,
        )

        await loadVersions(
          selectedForm.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible crear una nueva versión.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const selectVersion =
    async (
      version: FormVersion,
    ) => {
      setError('')
      setSuccess('')

      setSelectedVersionId(
        version.id,
      )

      setOptionField(
        null,
      )

      resetFieldEditor()
      resetOptionEditor()

      try {
        await loadFields(
          version.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cargar los campos de la versión.',
          ),
        )
      }
    }


  const publishVersion =
    async () => {
      if (
        !selectedVersion ||
        selectedVersion.status !==
          'draft'
      ) {
        return
      }

      setError('')
      setSuccess('')

      if (
        fields.length === 0
      ) {
        setError(
          'No puedes publicar una versión sin campos.',
        )

        return
      }

      const confirmed =
        window.confirm(
          `¿Deseas publicar la versión ${selectedVersion.version_number}? La versión publicada anteriormente quedará archivada.`,
        )

      if (!confirmed) {
        return
      }

      try {
        setIsSaving(
          true,
        )

        await publishFormVersion(
          selectedVersion.id,
        )

        setSuccess(
          `Versión ${selectedVersion.version_number} publicada correctamente.`,
        )

        if (selectedForm) {
          await loadVersions(
            selectedForm.id,
          )
        }
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible publicar la versión.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const handleFieldSubmit =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      if (
        !selectedVersion ||
        selectedVersion.status !==
          'draft'
      ) {
        return
      }

      setError('')
      setSuccess('')

      const name =
        fieldEditor.name.trim()

      if (!name) {
        setError(
          'El nombre del campo es obligatorio.',
        )

        return
      }

      try {
        setIsSaving(
          true,
        )

        if (
          editingFieldId ===
          null
        ) {
          await createFormField({
            form_version_id:
              selectedVersion.id,

            name,

            field_type:
              fieldEditor.field_type,

            field_order:
              fields.length + 1,

            is_required:
              fieldEditor.is_required,
          })

          setSuccess(
            'Campo agregado correctamente.',
          )
        } else {
          await updateFormField(
            editingFieldId,
            {
              name,

              is_required:
                fieldEditor.is_required,
            },
          )

          setSuccess(
            'Campo actualizado correctamente.',
          )
        }

        resetFieldEditor()

        await loadFields(
          selectedVersion.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible guardar el campo.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const startEditingField =
    (
      field: FormField,
    ) => {
      setError('')
      setSuccess('')

      setEditingFieldId(
        field.id,
      )

      setFieldEditor({
        name:
          field.name,

        field_type:
          field.field_type,

        is_required:
          field.is_required,
      })
    }


  const removeField =
    async (
      field: FormField,
    ) => {
      if (
        !selectedVersion ||
        selectedVersion.status !==
          'draft'
      ) {
        return
      }

      const confirmed =
        window.confirm(
          `¿Deseas eliminar el campo "${field.name}"?`,
        )

      if (!confirmed) {
        return
      }

      setError('')
      setSuccess('')

      try {
        await deleteFormField(
          field.id,
        )

        if (
          optionField?.id ===
          field.id
        ) {
          setOptionField(
            null,
          )

          setOptions(
            [],
          )
        }

        setSuccess(
          'Campo eliminado correctamente.',
        )

        await loadFields(
          selectedVersion.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible eliminar el campo.',
          ),
        )
      }
    }


  const moveField =
    async (
      field: FormField,
      direction: 'up' | 'down',
    ) => {
      if (
        !selectedVersion ||
        selectedVersion.status !==
          'draft'
      ) {
        return
      }

      const newOrder =
        direction === 'up'
          ? field.field_order - 1
          : field.field_order + 1

      if (
        newOrder < 1 ||
        newOrder >
          fields.length
      ) {
        return
      }

      setError('')
      setSuccess('')

      try {
        await reorderFormField(
          field.id,
          {
            new_order:
              newOrder,
          },
        )

        await loadFields(
          selectedVersion.id,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible reordenar el campo.',
          ),
        )
      }
    }


  const openOptions =
    async (
      field: FormField,
    ) => {
      setError('')
      setSuccess('')

      setOptionField(
        field,
      )

      resetOptionEditor()

      try {
        const loadedOptions =
          await getFieldOptions(
            field.id,
          )

        setOptions(
          loadedOptions,
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible cargar las opciones del campo.',
          ),
        )
      }
    }


  const handleOptionSubmit =
    async (
      event:
      FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      if (
        !optionField ||
        !selectedVersion ||
        selectedVersion.status !==
          'draft'
      ) {
        return
      }

      setError('')
      setSuccess('')

      const label =
        optionEditor.label.trim()

      const value =
        optionEditor.value.trim()

      if (
        !label ||
        !value
      ) {
        setError(
          'La etiqueta y el valor de la opción son obligatorios.',
        )

        return
      }

      try {
        setIsSaving(
          true,
        )

        if (
          editingOptionId ===
          null
        ) {
          await createFieldOption({
            form_field_id:
              optionField.id,

            label,

            value,

            option_order:
              options.length + 1,
          })

          setSuccess(
            'Opción agregada correctamente.',
          )
        } else {
          await updateFieldOption(
            editingOptionId,
            {
              label,
              value,
            },
          )

          setSuccess(
            'Opción actualizada correctamente.',
          )
        }

        resetOptionEditor()

        setOptions(
          await getFieldOptions(
            optionField.id,
          ),
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible guardar la opción.',
          ),
        )
      } finally {
        setIsSaving(
          false,
        )
      }
    }


  const startEditingOption =
    (
      option: FieldOption,
    ) => {
      setEditingOptionId(
        option.id,
      )

      setOptionEditor({
        label:
          option.label,

        value:
          option.value,
      })
    }


  const removeOption =
    async (
      option: FieldOption,
    ) => {
      if (!optionField) {
        return
      }

      const confirmed =
        window.confirm(
          `¿Deseas eliminar la opción "${option.label}"?`,
        )

      if (!confirmed) {
        return
      }

      setError('')
      setSuccess('')

      try {
        await deleteFieldOption(
          option.id,
        )

        setSuccess(
          'Opción eliminada correctamente.',
        )

        setOptions(
          await getFieldOptions(
            optionField.id,
          ),
        )
      } catch (
        requestError
      ) {
        setError(
          getApiErrorMessage(
            requestError,
            'No fue posible eliminar la opción.',
          ),
        )
      }
    }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando constructor...
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
            Constructor de formularios
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
                '/admin/projects',
              )
            }
          >
            Proyectos
          </button>
        </div>
      </header>

      <section className="content-container">
        <div className="page-heading">
          <div>
            <h1>
              Formularios
            </h1>

            <p>
              {project
                ? project.name
                : 'Proyecto'}
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
            {editingFormId ===
            null
              ? 'Crear formulario'
              : 'Editar formulario'}
          </h2>

          <form
            className="admin-form"
            onSubmit={
              handleFormSubmit
            }
          >
            <div className="form-field">
              <label>
                Nombre *
              </label>

              <input
                type="text"
                value={
                  formEditor.name
                }
                disabled={
                  isSaving
                }
                onChange={(
                  event,
                ) =>
                  setFormEditor(
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
              <label>
                Descripción
              </label>

              <textarea
                value={
                  formEditor
                    .description
                }
                disabled={
                  isSaving
                }
                onChange={(
                  event,
                ) =>
                  setFormEditor(
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
                {editingFormId ===
                null
                  ? 'Crear formulario'
                  : 'Guardar cambios'}
              </button>

              {editingFormId !==
                null && (
                <button
                  type="button"
                  className="outline-action"
                  onClick={
                    resetFormEditor
                  }
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="admin-list-section">
          <div className="page-heading">
            <div>
              <h2>
                Formularios del proyecto
              </h2>

              <p>
                {forms.length}
                {' '}
                {forms.length === 1
                  ? 'formulario'
                  : 'formularios'}
              </p>
            </div>
          </div>

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

                  <div className="admin-card-actions">
                    <button
                      type="button"
                      className="primary-action"
                      onClick={() =>
                        void openBuilder(
                          form,
                        )
                      }
                    >
                      Diseñar
                    </button>

                    <button
                      type="button"
                      className="outline-action"
                      onClick={() =>
                        startEditingForm(
                          form,
                        )
                      }
                    >
                      Editar
                    </button>

                    <button
                      type="button"
                      className="outline-action"
                      onClick={() =>
                        void toggleFormStatus(
                          form,
                        )
                      }
                    >
                      {form.is_active
                        ? 'Inactivar'
                        : 'Activar'}
                    </button>
                  </div>
                </article>
              ),
            )}
          </div>
        </section>

        {selectedForm && (
          <section className="admin-panel">
            <div className="page-heading">
              <div>
                <h2>
                  Constructor: {
                    selectedForm.name
                  }
                </h2>

                <p>
                  Administra versiones,
                  campos y opciones.
                </p>
              </div>

              <button
                type="button"
                className="primary-action"
                disabled={
                  hasDraft ||
                  isSaving
                }
                onClick={() =>
                  void createDraftVersion()
                }
              >
                Nueva versión
              </button>
            </div>

            {versions.length ===
              0 && (
              <div className="empty-state">
                <h2>
                  Sin versiones
                </h2>

                <p>
                  Crea una versión para
                  comenzar a diseñar la
                  encuesta.
                </p>
              </div>
            )}

            <div className="project-grid">
              {versions.map(
                (version) => (
                  <article
                    className="project-card"
                    key={
                      version.id
                    }
                  >
                    <div className="card-heading">
                      <h2>
                        Versión {
                          version
                            .version_number
                        }
                      </h2>

                      <span
                        className={
                          version.status ===
                          'published'
                            ? 'status status-active'
                            : 'status status-inactive'
                        }
                      >
                        {version.status ===
                        'draft'
                          ? 'Borrador'
                          : version.status ===
                            'published'
                            ? 'Publicada'
                            : 'Archivada'}
                      </span>
                    </div>

                    <button
                      type="button"
                      className={
                        selectedVersionId ===
                        version.id
                          ? 'primary-action'
                          : 'outline-action'
                      }
                      onClick={() =>
                        void selectVersion(
                          version,
                        )
                      }
                    >
                      {selectedVersionId ===
                      version.id
                        ? 'Versión seleccionada'
                        : 'Abrir versión'}
                    </button>
                  </article>
                ),
              )}
            </div>

            {selectedVersion && (
              <>
                <div className="page-heading">
                  <div>
                    <h2>
                      Versión {
                        selectedVersion
                          .version_number
                      }
                    </h2>

                    <p>
                      Estado: {
                        selectedVersion
                          .status
                      }
                    </p>
                  </div>

                  {selectedVersion.status ===
                    'draft' && (
                    <button
                      type="button"
                      className="primary-action"
                      disabled={
                        isSaving
                      }
                      onClick={() =>
                        void publishVersion()
                      }
                    >
                      Publicar versión
                    </button>
                  )}
                </div>

                {selectedVersion.status ===
                  'draft' && (
                  <form
                    className="admin-form"
                    onSubmit={
                      handleFieldSubmit
                    }
                  >
                    <h2>
                      {editingFieldId ===
                      null
                        ? 'Agregar campo'
                        : 'Editar campo'}
                    </h2>

                    <div className="admin-form-grid">
                      <div className="form-field">
                        <label>
                          Nombre *
                        </label>

                        <input
                          type="text"
                          value={
                            fieldEditor
                              .name
                          }
                          onChange={(
                            event,
                          ) =>
                            setFieldEditor(
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
                        <label>
                          Tipo
                        </label>

                        <select
                          value={
                            fieldEditor
                              .field_type
                          }
                          disabled={
                            editingFieldId !==
                            null
                          }
                          onChange={(
                            event,
                          ) =>
                            setFieldEditor(
                              (
                                current,
                              ) => ({
                                ...current,

                                field_type:
                                  event
                                    .target
                                    .value as FormFieldType,
                              }),
                            )
                          }
                        >
                          {Object.entries(
                            FIELD_TYPE_LABELS,
                          ).map(
                            ([
                              value,
                              label,
                            ]) => (
                              <option
                                key={
                                  value
                                }
                                value={
                                  value
                                }
                              >
                                {label}
                              </option>
                            ),
                          )}
                        </select>
                      </div>
                    </div>

                    <label className="checkbox-field">
                      <input
                        type="checkbox"
                        checked={
                          fieldEditor
                            .is_required
                        }
                        onChange={(
                          event,
                        ) =>
                          setFieldEditor(
                            (
                              current,
                            ) => ({
                              ...current,

                              is_required:
                                event
                                  .target
                                  .checked,
                            }),
                          )
                        }
                      />

                      Campo obligatorio
                    </label>

                    <div className="admin-actions">
                      <button
                        type="submit"
                        className="primary-action"
                      >
                        {editingFieldId ===
                        null
                          ? 'Agregar campo'
                          : 'Guardar campo'}
                      </button>

                      {editingFieldId !==
                        null && (
                        <button
                          type="button"
                          className="outline-action"
                          onClick={
                            resetFieldEditor
                          }
                        >
                          Cancelar
                        </button>
                      )}
                    </div>
                  </form>
                )}

                <div className="project-grid">
                  {fields.map(
                    (field) => (
                      <article
                        className="project-card"
                        key={
                          field.id
                        }
                      >
                        <div className="card-heading">
                          <h2>
                            {
                              field
                                .field_order
                            }. {
                              field.name
                            }
                          </h2>

                          <span className="status status-inactive">
                            {
                              FIELD_TYPE_LABELS[
                                field
                                  .field_type
                              ]
                            }
                          </span>
                        </div>

                        <p>
                          {field.is_required
                            ? 'Obligatorio'
                            : 'Opcional'}
                        </p>

                        {selectedVersion.status ===
                          'draft' && (
                          <div className="admin-card-actions">
                            <button
                              type="button"
                              className="outline-action"
                              disabled={
                                field.field_order ===
                                1
                              }
                              onClick={() =>
                                void moveField(
                                  field,
                                  'up',
                                )
                              }
                            >
                              ↑ Subir
                            </button>

                            <button
                              type="button"
                              className="outline-action"
                              disabled={
                                field.field_order ===
                                fields.length
                              }
                              onClick={() =>
                                void moveField(
                                  field,
                                  'down',
                                )
                              }
                            >
                              ↓ Bajar
                            </button>

                            <button
                              type="button"
                              className="primary-action"
                              onClick={() =>
                                startEditingField(
                                  field,
                                )
                              }
                            >
                              Editar
                            </button>

                            {field.field_type ===
                              'select' && (
                              <button
                                type="button"
                                className="outline-action"
                                onClick={() =>
                                  void openOptions(
                                    field,
                                  )
                                }
                              >
                                Opciones
                              </button>
                            )}

                            <button
                              type="button"
                              className="danger-action"
                              onClick={() =>
                                void removeField(
                                  field,
                                )
                              }
                            >
                              Eliminar
                            </button>
                          </div>
                        )}

                        {selectedVersion.status !==
                          'draft' &&
                          field.field_type ===
                            'select' && (
                            <button
                              type="button"
                              className="outline-action"
                              onClick={() =>
                                void openOptions(
                                  field,
                                )
                              }
                            >
                              Ver opciones
                            </button>
                          )}
                      </article>
                    ),
                  )}
                </div>

                {optionField && (
                  <section className="admin-panel">
                    <h2>
                      Opciones de {
                        optionField.name
                      }
                    </h2>

                    {selectedVersion.status ===
                      'draft' && (
                      <form
                        className="admin-form"
                        onSubmit={
                          handleOptionSubmit
                        }
                      >
                        <div className="admin-form-grid">
                          <div className="form-field">
                            <label>
                              Etiqueta *
                            </label>

                            <input
                              type="text"
                              value={
                                optionEditor
                                  .label
                              }
                              onChange={(
                                event,
                              ) =>
                                setOptionEditor(
                                  (
                                    current,
                                  ) => ({
                                    ...current,

                                    label:
                                      event
                                        .target
                                        .value,
                                  }),
                                )
                              }
                            />
                          </div>

                          <div className="form-field">
                            <label>
                              Valor *
                            </label>

                            <input
                              type="text"
                              value={
                                optionEditor
                                  .value
                              }
                              onChange={(
                                event,
                              ) =>
                                setOptionEditor(
                                  (
                                    current,
                                  ) => ({
                                    ...current,

                                    value:
                                      event
                                        .target
                                        .value,
                                  }),
                                )
                              }
                            />
                          </div>
                        </div>

                        <div className="admin-actions">
                          <button
                            type="submit"
                            className="primary-action"
                          >
                            {editingOptionId ===
                            null
                              ? 'Agregar opción'
                              : 'Guardar opción'}
                          </button>

                          {editingOptionId !==
                            null && (
                            <button
                              type="button"
                              className="outline-action"
                              onClick={
                                resetOptionEditor
                              }
                            >
                              Cancelar
                            </button>
                          )}
                        </div>
                      </form>
                    )}

                    <div className="project-grid">
                      {options.map(
                        (option) => (
                          <article
                            className="project-card"
                            key={
                              option.id
                            }
                          >
                            <div className="card-heading">
                              <h2>
                                {
                                  option
                                    .option_order
                                }. {
                                  option.label
                                }
                              </h2>
                            </div>

                            <p>
                              Valor: {
                                option.value
                              }
                            </p>

                            {selectedVersion.status ===
                              'draft' && (
                              <div className="admin-card-actions">
                                <button
                                  type="button"
                                  className="primary-action"
                                  onClick={() =>
                                    startEditingOption(
                                      option,
                                    )
                                  }
                                >
                                  Editar
                                </button>

                                <button
                                  type="button"
                                  className="danger-action"
                                  onClick={() =>
                                    void removeOption(
                                      option,
                                    )
                                  }
                                >
                                  Eliminar
                                </button>
                              </div>
                            )}
                          </article>
                        ),
                      )}
                    </div>

                    <button
                      type="button"
                      className="outline-action"
                      onClick={() => {
                        setOptionField(
                          null,
                        )

                        setOptions(
                          [],
                        )

                        resetOptionEditor()
                      }}
                    >
                      Cerrar opciones
                    </button>
                  </section>
                )}
              </>
            )}
          </section>
        )}
      </section>
    </main>
  )
}


export default AdminFormsPage