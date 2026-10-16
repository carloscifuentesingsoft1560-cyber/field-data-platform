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

import type {
  FieldOption,
} from '../types/fieldOption'

import type {
  Form,
} from '../types/form'

import type {
  FormField,
} from '../types/formField'

import type {
  FormVersion,
} from '../types/formVersion'


type FormValues = Record<
  number,
  string | boolean
>


function DynamicFormPage() {
  const navigate = useNavigate()

  const {
    projectId,
    formId,
  } = useParams()

  const [form, setForm] =
    useState<Form | null>(
      null,
    )

  const [version, setVersion] =
    useState<FormVersion | null>(
      null,
    )

  const [fields, setFields] =
    useState<FormField[]>([])

  const [options, setOptions] =
    useState<
      Record<number, FieldOption[]>
    >({})

  const [values, setValues] =
    useState<FormValues>({})

  const [isLoading, setIsLoading] =
    useState(true)

  const [error, setError] =
    useState('')


  useEffect(() => {
    const loadForm = async () => {
      const numericFormId =
        Number(formId)

      if (
        !formId ||
        Number.isNaN(
          numericFormId,
        )
      ) {
        setError(
          'El formulario seleccionado no es válido.',
        )

        setIsLoading(false)

        return
      }

      try {
        const [
          formResponse,
          versionsResponse,
        ] = await Promise.all([
          api.get<Form>(
            `/forms/${numericFormId}`,
          ),
          api.get<FormVersion[]>(
            `/form-versions/form/${numericFormId}`,
          ),
        ])

        setForm(
          formResponse.data,
        )

        const publishedVersion =
          versionsResponse.data.find(
            (item) =>
              item.status ===
              'published',
          )

        if (!publishedVersion) {
          setError(
            'Este formulario no tiene una versión publicada.',
          )

          return
        }

        setVersion(
          publishedVersion,
        )

        const fieldsResponse =
          await api.get<FormField[]>(
            `/form-fields/version/${publishedVersion.id}`,
          )

        const loadedFields =
          fieldsResponse.data

        setFields(
          loadedFields,
        )

        const selectFields =
          loadedFields.filter(
            (field) =>
              field.field_type ===
              'select',
          )

        const optionEntries =
          await Promise.all(
            selectFields.map(
              async (field) => {
                const response =
                  await api.get<
                    FieldOption[]
                  >(
                    `/field-options/by-field/${field.id}`,
                  )

                return [
                  field.id,
                  response.data,
                ] as const
              },
            ),
          )

        setOptions(
          Object.fromEntries(
            optionEntries,
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
              'No tienes acceso al formulario solicitado.',
            )

            return
          }
        }

        setError(
          'No fue posible cargar el formulario.',
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadForm()
  }, [
    formId,
    navigate,
  ])


  const updateValue = (
    fieldId: number,
    value: string | boolean,
  ) => {
    setValues(
      (currentValues) => ({
        ...currentValues,
        [fieldId]: value,
      }),
    )
  }


  if (isLoading) {
    return (
      <main className="center-page">
        <p>
          Cargando formulario...
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
            Captura de información
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() =>
            navigate(
              `/projects/${projectId}`,
            )
          }
        >
          Volver a formularios
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
          form &&
          version && (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    {form.name}
                  </h1>

                  <p>
                    Versión
                    {' '}
                    {version.version_number}
                  </p>
                </div>
              </div>

              <form
                className="dynamic-form"
                onSubmit={(event) =>
                  event.preventDefault()
                }
              >
                {fields.map(
                  (field) => (
                    <div
                      className="form-field"
                      key={field.id}
                    >
                      <label
                        htmlFor={
                          `field-${field.id}`
                        }
                      >
                        {field.name}

                        {field.is_required &&
                          ' *'}
                      </label>

                      {field.field_type ===
                        'text' && (
                        <input
                          id={
                            `field-${field.id}`
                          }
                          type="text"
                          required={
                            field.is_required
                          }
                          value={
                            String(
                              values[
                                field.id
                              ] ?? '',
                            )
                          }
                          onChange={(
                            event,
                          ) =>
                            updateValue(
                              field.id,
                              event.target
                                .value,
                            )
                          }
                        />
                      )}

                      {field.field_type ===
                        'textarea' && (
                        <textarea
                          id={
                            `field-${field.id}`
                          }
                          required={
                            field.is_required
                          }
                          value={
                            String(
                              values[
                                field.id
                              ] ?? '',
                            )
                          }
                          onChange={(
                            event,
                          ) =>
                            updateValue(
                              field.id,
                              event.target
                                .value,
                            )
                          }
                        />
                      )}

                      {field.field_type ===
                        'number' && (
                        <input
                          id={
                            `field-${field.id}`
                          }
                          type="number"
                          required={
                            field.is_required
                          }
                          value={
                            String(
                              values[
                                field.id
                              ] ?? '',
                            )
                          }
                          onChange={(
                            event,
                          ) =>
                            updateValue(
                              field.id,
                              event.target
                                .value,
                            )
                          }
                        />
                      )}

                      {field.field_type ===
                        'date' && (
                        <input
                          id={
                            `field-${field.id}`
                          }
                          type="date"
                          required={
                            field.is_required
                          }
                          value={
                            String(
                              values[
                                field.id
                              ] ?? '',
                            )
                          }
                          onChange={(
                            event,
                          ) =>
                            updateValue(
                              field.id,
                              event.target
                                .value,
                            )
                          }
                        />
                      )}

                      {field.field_type ===
                        'boolean' && (
                        <label className="checkbox-field">
                          <input
                            id={
                              `field-${field.id}`
                            }
                            type="checkbox"
                            checked={
                              Boolean(
                                values[
                                  field.id
                                ],
                              )
                            }
                            onChange={(
                              event,
                            ) =>
                              updateValue(
                                field.id,
                                event.target
                                  .checked,
                              )
                            }
                          />

                          Sí
                        </label>
                      )}

                      {field.field_type ===
                        'select' && (
                        <select
                          id={
                            `field-${field.id}`
                          }
                          required={
                            field.is_required
                          }
                          value={
                            String(
                              values[
                                field.id
                              ] ?? '',
                            )
                          }
                          onChange={(
                            event,
                          ) =>
                            updateValue(
                              field.id,
                              event.target
                                .value,
                            )
                          }
                        >
                          <option value="">
                            Seleccione una opción
                          </option>

                          {(
                            options[
                              field.id
                            ] ?? []
                          ).map(
                            (option) => (
                              <option
                                key={
                                  option.id
                                }
                                value={
                                  option.value
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
                  ),
                )}

                {fields.length === 0 && (
                  <div className="empty-state">
                    <h2>
                      Sin campos
                    </h2>

                    <p>
                      La versión publicada
                      no tiene campos
                      configurados.
                    </p>
                  </div>
                )}

                {fields.length > 0 && (
                  <button
                    className="primary-action"
                    type="submit"
                  >
                    Guardar encuesta
                  </button>
                )}
              </form>
            </>
          )}
      </section>
    </main>
  )
}


export default DynamicFormPage