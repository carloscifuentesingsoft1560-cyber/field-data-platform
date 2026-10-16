import type {
  SurveyAnswerCorrection,
  SurveyNumberValue,
} from './surveyAnswer'


export interface SurveyDetailAnswer {
  answer_id: number | null

  form_field_id: number
  field_name: string
  field_type: string
  field_order: number
  is_required: boolean

  answered: boolean

  value_text: string | null
  value_number: SurveyNumberValue
  value_date: string | null
  value_boolean: boolean | null

  field_option_id: number | null
  option_label: string | null
  option_value: string | null

  was_corrected: boolean
  correction_count: number

  corrections: SurveyAnswerCorrection[]
}


export interface SurveyDetailResponse {
  id: number
  uuid: string

  project_id: number

  form_id: number
  form_name: string

  form_version_id: number
  version_number: number

  user_id: number
  employee_number: string

  status: string

  latitude: number | null
  longitude: number | null

  captured_at: string
  received_at: string

  answers: SurveyDetailAnswer[]
}