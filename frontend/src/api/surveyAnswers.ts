import api from './client'

import type {
  SurveyAnswer,
  SurveyAnswerCorrectionResult,
  SurveyAnswerUpdatePayload,
} from '../types/surveyAnswer'


export async function getSurveyAnswers(
  surveyId: number,
): Promise<SurveyAnswer[]> {
  const response =
    await api.get<SurveyAnswer[]>(
      `/survey-answers/by-survey/${surveyId}`,
    )

  return response.data
}


export async function getSurveyAnswer(
  answerId: number,
): Promise<SurveyAnswer> {
  const response =
    await api.get<SurveyAnswer>(
      `/survey-answers/${answerId}`,
    )

  return response.data
}


export async function correctSurveyAnswer(
  answerId: number,
  payload:
    SurveyAnswerUpdatePayload,
): Promise<SurveyAnswerCorrectionResult> {
  const response =
    await api.patch<
      SurveyAnswerCorrectionResult
    >(
      `/survey-answers/${answerId}`,
      payload,
    )

  return response.data
}