export interface Form {
  id: number
  project_id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
}