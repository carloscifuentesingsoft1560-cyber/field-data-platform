import api from './client'

import type {
  FormVersion,
  FormVersionCreate,
} from '../types/formVersion'


export async function
getFormVersions(
  formId: number,
): Promise<FormVersion[]> {
  const response =
    await api.get<FormVersion[]>(
      `/form-versions/form/${formId}`,
    )

  return response.data
}


export async function
createFormVersion(
  data: FormVersionCreate,
): Promise<FormVersion> {
  const response =
    await api.post<FormVersion>(
      '/form-versions/',
      data,
    )

  return response.data
}


export async function
publishFormVersion(
  versionId: number,
): Promise<FormVersion> {
  const response =
    await api.patch<FormVersion>(
      `/form-versions/${versionId}/publish`,
    )

  return response.data
}