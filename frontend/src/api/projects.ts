import api from './client'

import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
} from '../types/project'


export async function getProjects():
Promise<Project[]> {
  const response =
    await api.get<Project[]>(
      '/projects',
    )

  return response.data
}


export async function createProject(
  data: ProjectCreate,
): Promise<Project> {
  const response =
    await api.post<Project>(
      '/projects',
      data,
    )

  return response.data
}


export async function updateProject(
  projectId: number,
  data: ProjectUpdate,
): Promise<Project> {
  const response =
    await api.patch<Project>(
      `/projects/${projectId}`,
      data,
    )

  return response.data
}


export async function deleteProject(
  projectId: number,
): Promise<void> {
  await api.delete(
    `/projects/${projectId}`,
  )
}