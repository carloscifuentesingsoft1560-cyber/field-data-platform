export interface LoginRequest {
  employee_number: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthUser {
  id: number
  employee_number: string
  identification: string
  role_id: number
  role_name: string
  is_active: boolean
}