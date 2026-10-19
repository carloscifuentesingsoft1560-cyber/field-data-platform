export interface User {
  id: number
  employee_number: string
  identification: string
  role_id: number
  is_active: boolean
  created_at: string
}


export interface UserCreate {
  employee_number: string
  identification: string
  password: string
  role_id: number
}


export interface UserUpdate {
  employee_number?: string
  identification?: string
  role_id?: number
  is_active?: boolean
}