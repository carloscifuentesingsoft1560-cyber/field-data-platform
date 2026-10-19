export type ProjectStatus =
  'active' | 'inactive'


export interface Project {
  id: number
  name: string
  description: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
  start_date: string
  end_date: string | null
}


export interface ProjectCreate {
  name: string
  description: string | null
  status: ProjectStatus
  start_date: string
  end_date: string | null
}


export interface ProjectUpdate {
  name?: string
  description?: string | null
  status?: ProjectStatus
  start_date?: string
  end_date?: string | null
}