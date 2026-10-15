export interface Project {
  id: number
  name: string
  description: string | null
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
  start_date: string
  end_date: string | null
}