import api from './client'

import type {
  UserProject,
  UserProjectCreate,
} from '../types/userProject'


export async function
getUserProjects(
  userId: number,
): Promise<UserProject[]> {
  const response =
    await api.get<UserProject[]>(
      `/user-projects/user/${userId}`,
    )

  return response.data
}


export async function
assignUserProject(
  data: UserProjectCreate,
): Promise<UserProject> {
  const response =
    await api.post<UserProject>(
      '/user-projects/',
      data,
    )

  return response.data
}


export async function
removeUserProject(
  userId: number,
  projectId: number,
): Promise<void> {
  await api.delete(
    `/user-projects/${userId}/${projectId}`,
  )
}