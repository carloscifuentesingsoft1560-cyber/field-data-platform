import api from './client'

import type {
  AuthUser,
  LoginRequest,
  TokenResponse,
} from '../types/auth'


const ACCESS_TOKEN_KEY = 'access_token'
const TOKEN_EXPIRES_AT_KEY =
  'token_expires_at'


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


export async function getCurrentUser():
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
}


export function clearSession(): void {
  localStorage.removeItem(
    ACCESS_TOKEN_KEY,
  )

  localStorage.removeItem(
    TOKEN_EXPIRES_AT_KEY,
  )
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

  if (!token || !expiresAtValue) {
    clearSession()
    return false
  }

  const expiresAt =
    Number(expiresAtValue)

  if (
    Number.isNaN(expiresAt) ||
    Date.now() >= expiresAt
  ) {
    clearSession()
    return false
  }

  return true
}