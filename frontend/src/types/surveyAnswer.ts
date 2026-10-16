export type SurveyNumberValue =
  string | number | null


export interface SurveyAnswer {
  id: number
  survey_id: number
  form_field_id: number

  value_text: string | null
  value_number: SurveyNumberValue
  value_date: string | null
  value_boolean: boolean | null
  field_option_id: number | null

  created_at: string
}


export interface SurveyAnswerUpdatePayload {
  reason: string

  value_text?: string | null
  value_number?: number | null
  value_date?: string | null
  value_boolean?: boolean | null
  field_option_id?: number | null
}


export interface SurveyAnswerCorrection {
  id: number
  survey_answer_id: number
  corrected_by_user_id: number

  old_value_text: string | null
  old_value_number: SurveyNumberValue
  old_value_date: string | null
  old_value_boolean: boolean | null
  old_field_option_id: number | null

  new_value_text: string | null
  new_value_number: SurveyNumberValue
  new_value_date: string | null
  new_value_boolean: boolean | null
  new_field_option_id: number | null

  reason: string | null
  corrected_at: string
}


export interface SurveyAnswerCorrectionResult {
  answer: SurveyAnswer
  correction: SurveyAnswerCorrection
}