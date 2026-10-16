import Dexie, {
  type EntityTable,
} from 'dexie'

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


const db = new Dexie(
  'FieldDataPlatformDB',
) as Dexie & {
  pendingSurveys: EntityTable<
    PendingSurvey,
    'uuid'
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


export default db