import api from './client'

import type {
  User,
  UserCreate,
  UserUpdate,
} from '../types/user'


export async function getUsers():
Promise<User[]> {
  const response =
    await api.get<User[]>(
      '/users/',
    )

  return response.data
}


export async function createUser(
  data: UserCreate,
): Promise<User> {
  const response =
    await api.post<User>(
      '/users/',
      data,
    )

  return response.data
}


export async function updateUser(
  userId: number,
  data: UserUpdate,
): Promise<User> {
  const response =
    await api.patch<User>(
      `/users/${userId}`,
      data,
    )

  return response.data
}


export async function
resetUserPassword(
  userId: number,
  newPassword: string,
): Promise<void> {
  await api.patch(
    `/users/${userId}/reset-password`,
    {
      new_password:
        newPassword,
    },
  )
}