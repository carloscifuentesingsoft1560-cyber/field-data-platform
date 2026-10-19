import axios from 'axios'

import {
  ACCESS_TOKEN_KEY,
  clearStoredSession,
  markSessionExpired,
} from './session'


const API_URL =
  import.meta.env.VITE_API_URL ??
  'http://127.0.0.1:8000'


const api = axios.create({
  baseURL: API_URL,

  headers: {
    'Content-Type':
      'application/json',
  },
})


api.interceptors.request.use(
  (config) => {
    const token =
      localStorage.getItem(
        ACCESS_TOKEN_KEY,
      )

    if (token) {
      config.headers.Authorization =
        `Bearer ${token}`
    }

    return config
  },
)


api.interceptors.response.use(
  (response) =>
    response,

  (error: unknown) => {
    if (
      axios.isAxiosError(
        error,
      )
    ) {
      const status =
        error.response
          ?.status

      const requestUrl =
        error.config
          ?.url ?? ''

      const isLoginRequest =
        requestUrl.includes(
          '/auth/login',
        )

      if (
        status === 401 &&
        !isLoginRequest
      ) {
        clearStoredSession()

        markSessionExpired()

        if (
          window.location.pathname !==
          '/login'
        ) {
          window.location.replace(
            '/login?expired=1',
          )
        }
      }
    }

    return Promise.reject(
      error,
    )
  },
)


export default api