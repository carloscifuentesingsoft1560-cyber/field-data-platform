import api from './client'

import type {
  SurveyRecord,
  SurveySyncPayload,
  SurveySyncResponse,
} from '../types/survey'

import type {
  SurveyDetailResponse,
} from '../types/surveyDetail'


export async function getSurveys():
Promise<SurveyRecord[]> {
  const response =
    await api.get<SurveyRecord[]>(
      '/surveys/',
    )

  return response.data
}


export async function getSurveyByUuid(
  surveyUuid: string,
): Promise<SurveyRecord> {
  const response =
    await api.get<SurveyRecord>(
      `/surveys/by-uuid/${surveyUuid}`,
    )

  return response.data
}


export async function getSurveyDetail(
  surveyId: number,
): Promise<SurveyDetailResponse> {
  const response =
    await api.get<SurveyDetailResponse>(
      `/surveys/${surveyId}/detail`,
    )

  return response.data
}


export async function syncSurvey(
  payload: SurveySyncPayload,
): Promise<SurveySyncResponse> {
  const response =
    await api.post<SurveySyncResponse>(
      '/surveys/sync',
      payload,
    )

  return response.data
}