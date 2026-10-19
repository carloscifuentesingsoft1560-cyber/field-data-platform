import api from './client'

import {
  ACCESS_TOKEN_KEY,
  TOKEN_EXPIRES_AT_KEY,
  clearSessionExpired,
  clearStoredSession,
  markSessionExpired,
} from './session'

import type {
  AuthUser,
  LoginRequest,
  TokenResponse,
} from '../types/auth'


export async function login(
  credentials: LoginRequest,
): Promise<TokenResponse> {
  const response =
    await api.post<TokenResponse>(
      '/auth/login',
      credentials,
    )

  return response.data
}


export async function
getCurrentUser():
Promise<AuthUser> {
  const response =
    await api.get<AuthUser>(
      '/auth/me',
    )

  return response.data
}


export function saveSession(
  tokenData: TokenResponse,
): void {
  const expiresAt =
    Date.now() +
    tokenData.expires_in * 1000

  localStorage.setItem(
    ACCESS_TOKEN_KEY,
    tokenData.access_token,
  )

  localStorage.setItem(
    TOKEN_EXPIRES_AT_KEY,
    expiresAt.toString(),
  )

  clearSessionExpired()
}


export function clearSession():
void {
  clearStoredSession()
}


export function getSessionUserId():
number | null {
  const token =
    localStorage.getItem(
      ACCESS_TOKEN_KEY,
    )

  if (!token) {
    return null
  }

  try {
    const parts =
      token.split('.')

    if (
      parts.length !== 3
    ) {
      return null
    }

    const normalized =
      parts[1]
        .replace(
          /-/g,
          '+',
        )
        .replace(
          /_/g,
          '/',
        )

    const padded =
      normalized.padEnd(
        Math.ceil(
          normalized.length /
            4,
        ) * 4,
        '=',
      )

    const payload =
      JSON.parse(
        atob(
          padded,
        ),
      ) as {
        sub?: string
      }

    if (!payload.sub) {
      return null
    }

    const userId =
      Number(
        payload.sub,
      )

    if (
      Number.isNaN(
        userId,
      )
    ) {
      return null
    }

    return userId
  } catch {
    return null
  }
}


export function hasValidSession():
boolean {
  const token =
    localStorage.getItem(
      ACCESS_TOKEN_KEY,
    )

  const expiresAtValue =
    localStorage.getItem(
      TOKEN_EXPIRES_AT_KEY,
    )

  if (
    !token ||
    !expiresAtValue
  ) {
    clearStoredSession()

    return false
  }

  const expiresAt =
    Number(
      expiresAtValue,
    )

  if (
    Number.isNaN(
      expiresAt,
    )
  ) {
    clearStoredSession()

    return false
  }

  if (
    Date.now() >=
    expiresAt
  ) {
    clearStoredSession()

    markSessionExpired()

    return false
  }

  return true
}