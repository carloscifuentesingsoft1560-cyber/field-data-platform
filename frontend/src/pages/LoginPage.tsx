import {
  type FormEvent,
  useState,
} from 'react'

import axios from 'axios'

import {
  Navigate,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'

import {
  clearSession,
  hasValidSession,
  login,
  saveSession,
} from '../api/auth'

import {
  hasSessionExpired,
} from '../api/session'


interface ApiError {
  detail?: string
}


function LoginPage() {
  const navigate =
    useNavigate()

  const [
    searchParams,
  ] =
    useSearchParams()

  const [
    username,
    setUsername,
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


  const validSession =
    hasValidSession()

  const sessionExpired =
    searchParams.get(
      'expired',
    ) === '1' ||
    hasSessionExpired()


  if (validSession) {
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
        !username.trim() ||
        !password
      ) {
        setError(
          'Ingrese el usuario y la contraseña.',
        )

        return
      }

      try {
        setIsLoading(
          true,
        )

        const tokenData =
          await login({
            employee_number:
              username.trim(),

            password,
          })

        saveSession(
          tokenData,
        )

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
        setIsLoading(
          false,
        )
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

          {sessionExpired && (
            <div
              className="alert alert-offline"
              role="status"
            >
              Tu sesión expiró.
              Inicia sesión nuevamente.
            </div>
          )}

          <label>
            Usuario

            <input
              type="text"
              value={
                username
              }
              onChange={(
                event,
              ) =>
                setUsername(
                  event.target.value,
                )
              }
              autoComplete="username"
              disabled={
                isLoading
              }
              placeholder="Ej. CARLOS01"
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

          <div
            className="alert alert-offline"
            role="note"
          >
            ¿Olvidaste tu contraseña?
            Solicita al Director o al
            Jefe Nacional el
            restablecimiento de tu acceso.
          </div>
        </form>
      </section>
    </main>
  )
}


export default LoginPage