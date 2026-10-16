import {
  type FormEvent,
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
  queueSurvey,
  syncQueuedSurvey,
} from '../services/surveyQueue'

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

import type {
  SurveyAnswerPayload,
  SurveySyncPayload,
} from '../types/survey'


type FormValues = Record<
  number,
  string | boolean
>


interface Coordinates {
  latitude: number | null
  longitude: number | null
}


function getCoordinates():
Promise<Coordinates> {
  return new Promise(
    (resolve) => {
      if (
        !navigator.geolocation
      ) {
        resolve({
          latitude: null,
          longitude: null,
        })

        return
      }

      navigator.geolocation
        .getCurrentPosition(
          (position) => {
            resolve({
              latitude:
                position.coords
                  .latitude,

              longitude:
                position.coords
                  .longitude,
            })
          },

          () => {
            resolve({
              latitude: null,
              longitude: null,
            })
          },

          {
            enableHighAccuracy: true,
            timeout: 8000,
            maximumAge: 60000,
          },
        )
    },
  )
}


function buildInitialValues(
  fields: FormField[],
): FormValues {
  const initialValues:
  FormValues = {}

  for (
    const field of fields
  ) {
    if (
      field.field_type ===
      'boolean'
    ) {
      initialValues[
        field.id
      ] = false
    }
  }

  return initialValues
}


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

  const [isSaving, setIsSaving] =
    useState(false)

  const [error, setError] =
    useState('')

  const [success, setSuccess] =
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

        setValues(
          buildInitialValues(
            loadedFields,
          ),
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


  const resetFormValues = () => {
    setValues(
      buildInitialValues(
        fields,
      ),
    )
  }


  const buildAnswers = ():
  SurveyAnswerPayload[] => {
    const answers:
    SurveyAnswerPayload[] = []

    for (
      const field of fields
    ) {
      const value =
        values[field.id]

      const isEmpty =
        value === undefined ||
        value === null ||
        value === ''

      if (
        field.is_required &&
        isEmpty &&
        field.field_type !==
          'boolean'
      ) {
        throw new Error(
          `El campo "${field.name}" es obligatorio.`,
        )
      }

      if (
        !field.is_required &&
        isEmpty &&
        field.field_type !==
          'boolean'
      ) {
        continue
      }

      if (
        field.field_type ===
          'text' ||
        field.field_type ===
          'textarea'
      ) {
        answers.push({
          form_field_id:
            field.id,

          value_text:
            String(value),
        })
      }

      if (
        field.field_type ===
        'number'
      ) {
        const numericValue =
          Number(value)

        if (
          Number.isNaN(
            numericValue,
          )
        ) {
          throw new Error(
            `El campo "${field.name}" debe contener un número válido.`,
          )
        }

        answers.push({
          form_field_id:
            field.id,

          value_number:
            numericValue,
        })
      }

      if (
        field.field_type ===
        'date'
      ) {
        answers.push({
          form_field_id:
            field.id,

          value_date:
            String(value),
        })
      }

      if (
        field.field_type ===
        'boolean'
      ) {
        answers.push({
          form_field_id:
            field.id,

          value_boolean:
            Boolean(value),
        })
      }

      if (
        field.field_type ===
        'select'
      ) {
        const optionId =
          Number(value)

        if (
          Number.isNaN(
            optionId,
          )
        ) {
          throw new Error(
            `Seleccione una opción válida en "${field.name}".`,
          )
        }

        answers.push({
          form_field_id:
            field.id,

          field_option_id:
            optionId,
        })
      }
    }

    return answers
  }


  const handleSubmit = async (
    event:
    FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setError('')
    setSuccess('')

    if (!version) {
      setError(
        'No se encontró una versión publicada.',
      )

      return
    }

    try {
      setIsSaving(true)

      const answers =
        buildAnswers()

      const coordinates =
        await getCoordinates()

      const payload:
      SurveySyncPayload = {
        uuid:
          crypto.randomUUID(),

        form_version_id:
          version.id,

        latitude:
          coordinates.latitude,

        longitude:
          coordinates.longitude,

        captured_at:
          new Date()
            .toISOString(),

        answers,
      }

      /*
       * Primero se almacena localmente.
       * Así no se pierde la encuesta si
       * la conexión falla durante el envío.
       */
      await queueSurvey(
        payload,
      )

      /*
       * Si el navegador ya sabe que está
       * sin conexión, dejamos la encuesta
       * pendiente en IndexedDB.
       */
      if (!navigator.onLine) {
        setSuccess(
          'Encuesta guardada en el dispositivo. Se sincronizará automáticamente cuando vuelva la conexión.',
        )

        resetFormValues()

        return
      }

      try {
        const result =
          await syncQueuedSurvey(
            payload,
          )

        setSuccess(
          `Encuesta guardada y sincronizada correctamente. Identificación: ${result.survey.id}`,
        )

        resetFormValues()
      } catch (syncError) {
        /*
         * No hubo respuesta del servidor:
         * conservamos la encuesta localmente.
         */
        if (
          axios.isAxiosError(
            syncError,
          ) &&
          !syncError.response
        ) {
          setSuccess(
            'Encuesta guardada en el dispositivo. No fue posible contactar el servidor y queda pendiente de sincronización.',
          )

          resetFormValues()

          return
        }

        /*
         * Sesión vencida. La encuesta sigue
         * en IndexedDB asociada al usuario.
         */
        if (
          axios.isAxiosError(
            syncError,
          ) &&
          syncError.response
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
            syncError,
          )
        ) {
          const detail =
            syncError.response
              ?.data?.detail

          setError(
            typeof detail ===
              'string'
              ? detail
              : 'La encuesta quedó guardada localmente, pero el servidor rechazó la sincronización.',
          )

          return
        }

        throw syncError
      }
    } catch (requestError) {
      if (
        requestError
          instanceof Error
      ) {
        setError(
          requestError.message,
        )

        return
      }

      setError(
        'Ocurrió un error inesperado al guardar la encuesta.',
      )
    } finally {
      setIsSaving(false)
    }
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

        {success && (
          <div
            className="alert alert-success"
            role="status"
          >
            {success}
          </div>
        )}

        {form &&
          version && (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    {form.name}
                  </h1>

                  <p>
                    Versión{' '}
                    {
                      version
                        .version_number
                    }
                  </p>
                </div>
              </div>

              <form
                className="dynamic-form"
                onSubmit={
                  handleSubmit
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
                        <label
                          className="checkbox-field"
                        >
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
                                  option.id
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

                {fields.length ===
                  0 && (
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

                {fields.length >
                  0 && (
                  <button
                    className="primary-action"
                    type="submit"
                    disabled={
                      isSaving
                    }
                  >
                    {isSaving
                      ? 'Guardando...'
                      : 'Guardar encuesta'}
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