import api from './client'

import type {
  Role,
} from '../types/role'


export async function getRoles():
Promise<Role[]> {
  const response =
    await api.get<Role[]>(
      '/roles/',
    )

  return response.data
}