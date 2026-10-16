import Dexie, {
  type EntityTable,
} from 'dexie'

import type {
  AuthUser,
} from '../types/auth'

import type {
  FieldOption,
} from '../types/fieldOption'

import type {
  Form,
} from '../types/form'

import type {
  FormField,
} from '../types/formField'

import type {
  FormVersion,
} from '../types/formVersion'

import type {
  Project,
} from '../types/project'

import type {
  SurveySyncPayload,
} from '../types/survey'


export interface PendingSurvey {
  uuid: string
  owner_user_id: number
  payload: SurveySyncPayload
  created_at: string
  attempts: number
  last_error: string | null
}


export interface CachedUser {
  owner_user_id: number
  data: AuthUser
  cached_at: string
}


export interface CachedProject {
  cache_key: string
  owner_user_id: number
  project_id: number
  data: Project
  cached_at: string
}


export interface CachedForm {
  cache_key: string
  owner_user_id: number
  project_id: number
  form_id: number
  data: Form
  cached_at: string
}


export interface CachedFormVersion {
  cache_key: string
  owner_user_id: number
  form_id: number
  version_id: number
  status: string
  data: FormVersion
  cached_at: string
}


export interface CachedFormField {
  cache_key: string
  owner_user_id: number
  form_version_id: number
  field_id: number
  field_order: number
  data: FormField
  cached_at: string
}


export interface CachedFieldOption {
  cache_key: string
  owner_user_id: number
  form_field_id: number
  option_id: number
  option_order: number
  data: FieldOption
  cached_at: string
}


const db = new Dexie(
  'FieldDataPlatformDB',
) as Dexie & {
  pendingSurveys: EntityTable<
    PendingSurvey,
    'uuid'
  >

  cachedUsers: EntityTable<
    CachedUser,
    'owner_user_id'
  >

  cachedProjects: EntityTable<
    CachedProject,
    'cache_key'
  >

  cachedForms: EntityTable<
    CachedForm,
    'cache_key'
  >

  cachedFormVersions: EntityTable<
    CachedFormVersion,
    'cache_key'
  >

  cachedFormFields: EntityTable<
    CachedFormField,
    'cache_key'
  >

  cachedFieldOptions: EntityTable<
    CachedFieldOption,
    'cache_key'
  >
}


db.version(1).stores({
  pendingSurveys:
    'uuid, created_at',
})


db.version(2).stores({
  pendingSurveys:
    'uuid, owner_user_id, created_at',
})


db.version(3).stores({
  pendingSurveys:
    'uuid, owner_user_id, created_at',

  cachedUsers:
    'owner_user_id, cached_at',

  cachedProjects:
    'cache_key, owner_user_id, project_id, cached_at',

  cachedForms:
    'cache_key, owner_user_id, project_id, form_id, cached_at',

  cachedFormVersions:
    'cache_key, owner_user_id, form_id, version_id, status, cached_at',

  cachedFormFields:
    'cache_key, owner_user_id, form_version_id, field_id, field_order, cached_at',

  cachedFieldOptions:
    'cache_key, owner_user_id, form_field_id, option_id, option_order, cached_at',
})


export default db