export interface FieldOption {
  id: number
  form_field_id: number
  label: string
  value: string
  option_order: number
}


export interface FieldOptionCreate {
  form_field_id: number
  label: string
  value: string
  option_order: number
}


export interface FieldOptionUpdate {
  label?: string
  value?: string
  option_order?: number
}