export type FormFieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'date'
  | 'boolean'
  | 'select'


export interface FormField {
  id: number
  form_version_id: number
  name: string
  field_type: FormFieldType
  field_order: number
  is_required: boolean
}