export interface SurveyAnswerPayload {
  form_field_id: number
  value_text?: string
  value_number?: number
  value_date?: string
  value_boolean?: boolean
  field_option_id?: number
}

export interface SurveySyncPayload {
  uuid: string
  form_version_id: number
  latitude: number | null
  longitude: number | null
  captured_at: string
  answers: SurveyAnswerPayload[]
}

export interface SurveySyncResponse {
  survey: {
    id: number
    uuid: string
    form_version_id: number
    user_id: number
    status: string
    latitude: number | null
    longitude: number | null
    captured_at: string
    received_at: string
  }
  answers: unknown[]
}