
import api from './client'

import type {
  FormField,
  FormFieldCreate,
  FormFieldReorder,
  FormFieldUpdate,
} from '../types/formField'


export async function
getFormFields(
  versionId: number,
): Promise<FormField[]> {
  const response =
    await api.get<FormField[]>(
      `/form-fields/version/${versionId}`,
    )

  return response.data
}


export async function
createFormField(
  data: FormFieldCreate,
): Promise<FormField> {
  const response =
    await api.post<FormField>(
      '/form-fields/',
      data,
    )

  return response.data
}


export async function
updateFormField(
  fieldId: number,
  data: FormFieldUpdate,
): Promise<FormField> {
  const response =
    await api.patch<FormField>(
      `/form-fields/${fieldId}`,
      data,
    )

  return response.data
}


export async function
deleteFormField(
  fieldId: number,
): Promise<void> {
  await api.delete(
    `/form-fields/${fieldId}`,
  )
}


export async function
reorderFormField(
  fieldId: number,
  data: FormFieldReorder,
): Promise<FormField> {
  const response =
    await api.patch<FormField>(
      `/form-fields/${fieldId}/reorder`,
      data,
    )

  return response.data
}