import api from './client'

import type {
  FieldOption,
  FieldOptionCreate,
  FieldOptionUpdate,
} from '../types/fieldOption'


export async function
getFieldOptions(
  fieldId: number,
): Promise<FieldOption[]> {
  const response =
    await api.get<FieldOption[]>(
      `/field-options/by-field/${fieldId}`,
    )

  return response.data
}


export async function
createFieldOption(
  data: FieldOptionCreate,
): Promise<FieldOption> {
  const response =
    await api.post<FieldOption>(
      '/field-options/',
      data,
    )

  return response.data
}


export async function
updateFieldOption(
  optionId: number,
  data: FieldOptionUpdate,
): Promise<FieldOption> {
  const response =
    await api.patch<FieldOption>(
      `/field-options/${optionId}`,
      data,
    )

  return response.data
}


export async function
deleteFieldOption(
  optionId: number,
): Promise<void> {
  await api.delete(
    `/field-options/${optionId}`,
  )
}