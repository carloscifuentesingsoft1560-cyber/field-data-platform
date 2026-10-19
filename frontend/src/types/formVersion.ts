export type FormVersionStatus =
  | 'draft'
  | 'published'
  | 'archived'


export interface FormVersion {
  id: number
  form_id: number
  version_number: number
  status: FormVersionStatus
  created_at: string
}


export interface FormVersionCreate {
  form_id: number
}