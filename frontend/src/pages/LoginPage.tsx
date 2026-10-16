import {
  type FormEvent,
  useState,
} from 'react'

import axios from 'axios'

import {
  Navigate,
  useNavigate,
} from 'react-router-dom'

import {
  clearSession,
  hasValidSession,
  login,
  saveSession,
} from '../api/auth'


interface ApiError {
  detail?: string
}


function LoginPage() {
  const navigate =
    useNavigate()

  const [
    employeeNumber,
    setEmployeeNumber,
  ] =
    useState('')

  const [
    password,
    setPassword,
  ] =
    useState('')

  const [
    error,
    setError,
  ] =
    useState('')

  const [
    isLoading,
    setIsLoading,
  ] =
    useState(false)


  if (hasValidSession()) {
    return (
      <Navigate
        to="/projects"
        replace
      />
    )
  }


  const handleSubmit =
    async (
      event:
        FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault()

      setError('')

      if (
        !employeeNumber.trim() ||
        !password
      ) {
        setError(
          'Ingrese el número de empleado y la contraseña.',
        )

        return
      }

      try {
        setIsLoading(true)

        const tokenData =
          await login({
            employee_number:
              employeeNumber.trim(),

            password,
          })

        saveSession(
          tokenData,
        )

        /*
         * ProjectsPage ya consulta
         * /auth/me al cargar.
         *
         * Evitamos hacer aquí una
         * consulta duplicada.
         */
        navigate(
          '/projects',
          {
            replace: true,
          },
        )
      } catch (
        requestError
      ) {
        clearSession()

        if (
          axios.isAxiosError<
            ApiError
          >(
            requestError,
          )
        ) {
          setError(
            requestError
              .response
              ?.data
              ?.detail ??
              'No fue posible iniciar sesión.',
          )
        } else {
          setError(
            'Ocurrió un error inesperado.',
          )
        }
      } finally {
        setIsLoading(false)
      }
    }


  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand">
          <span className="brand-badge">
            FDP
          </span>

          <div>
            <h1>
              Field Data Platform
            </h1>

            <p>
              Plataforma de captura y
              gestión de información
              en campo
            </p>
          </div>
        </div>

        <form
          className="login-form"
          onSubmit={
            handleSubmit
          }
        >
          <div>
            <h2>
              Iniciar sesión
            </h2>

            <p className="form-description">
              Ingresa con tus
              credenciales asignadas.
            </p>
          </div>

          <label>
            Número de empleado

            <input
              type="text"
              value={
                employeeNumber
              }
              onChange={(
                event,
              ) =>
                setEmployeeNumber(
                  event.target.value,
                )
              }
              autoComplete="username"
              disabled={
                isLoading
              }
            />
          </label>

          <label>
            Contraseña

            <input
              type="password"
              value={
                password
              }
              onChange={(
                event,
              ) =>
                setPassword(
                  event.target.value,
                )
              }
              autoComplete="current-password"
              disabled={
                isLoading
              }
            />
          </label>

          {error && (
            <div
              className="alert alert-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={
              isLoading
            }
          >
            {isLoading
              ? 'Ingresando...'
              : 'Ingresar'}
          </button>
        </form>
      </section>
    </main>
  )
}


export default LoginPage