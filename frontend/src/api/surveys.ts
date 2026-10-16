import api from './client'

import type {
  SurveySyncPayload,
  SurveySyncResponse,
} from '../types/survey'


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