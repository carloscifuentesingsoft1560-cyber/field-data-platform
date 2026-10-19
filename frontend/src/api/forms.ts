import api from './client'

import type {
  Form,
  FormCreate,
  FormUpdate,
} from '../types/form'


export async function getForms():
Promise<Form[]> {
  const response =
    await api.get<Form[]>(
      '/forms/',
    )

  return response.data
}


export async function createForm(
  data: FormCreate,
): Promise<Form> {
  const response =
    await api.post<Form>(
      '/forms/',
      data,
    )

  return response.data
}


export async function updateForm(
  formId: number,
  data: FormUpdate,
): Promise<Form> {
  const response =
    await api.patch<Form>(
      `/forms/${formId}`,
      data,
    )

  return response.data
}