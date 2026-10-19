export interface UserProject {
  id: number
  user_id: number
  project_id: number
}


export interface UserProjectCreate {
  user_id: number
  project_id: number
}