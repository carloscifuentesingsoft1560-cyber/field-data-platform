export const ACCESS_TOKEN_KEY =
  'access_token'

export const TOKEN_EXPIRES_AT_KEY =
  'token_expires_at'

export const SESSION_EXPIRED_KEY =
  'session_expired'


export function clearStoredSession():
void {
  localStorage.removeItem(
    ACCESS_TOKEN_KEY,
  )

  localStorage.removeItem(
    TOKEN_EXPIRES_AT_KEY,
  )
}


export function markSessionExpired():
void {
  sessionStorage.setItem(
    SESSION_EXPIRED_KEY,
    'true',
  )
}


export function hasSessionExpired():
boolean {
  return (
    sessionStorage.getItem(
      SESSION_EXPIRED_KEY,
    ) === 'true'
  )
}


export function clearSessionExpired():
void {
  sessionStorage.removeItem(
    SESSION_EXPIRED_KEY,
  )
}