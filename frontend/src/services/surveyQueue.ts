import axios from 'axios'

import {
  syncSurvey,
} from '../api/surveys'

import db from '../db/database'

import type {
  SurveySyncPayload,
  SurveySyncResponse,
} from '../types/survey'


let isSyncing = false


function getSessionUserId():
number | null {
  const token =
    localStorage.getItem(
      'access_token',
    )

  if (!token) {
    return null
  }

  try {
    const parts =
      token.split('.')

    if (parts.length !== 3) {
      return null
    }

    const normalized =
      parts[1]
        .replace(/-/g, '+')
        .replace(/_/g, '/')

    const padded =
      normalized.padEnd(
        Math.ceil(
          normalized.length / 4,
        ) * 4,
        '=',
      )

    const payload =
      JSON.parse(
        atob(padded),
      ) as {
        sub?: string
      }

    if (!payload.sub) {
      return null
    }

    const userId =
      Number(payload.sub)

    if (
      Number.isNaN(userId)
    ) {
      return null
    }

    return userId
  } catch {
    return null
  }
}


function getErrorMessage(
  error: unknown,
): string {
  if (
    axios.isAxiosError(error)
  ) {
    const detail =
      error.response
        ?.data?.detail

    if (
      typeof detail ===
      'string'
    ) {
      return detail
    }

    if (!error.response) {
      return (
        'Sin conexión con el servidor.'
      )
    }

    return (
      `Error HTTP ${
        error.response.status
      }`
    )
  }

  if (
    error instanceof Error
  ) {
    return error.message
  }

  return 'Error desconocido.'
}


export async function
queueSurvey(
  payload: SurveySyncPayload,
): Promise<void> {
  const ownerUserId =
    getSessionUserId()

  if (!ownerUserId) {
    throw new Error(
      'No fue posible identificar al usuario de la encuesta.',
    )
  }

  await db.pendingSurveys.put({
    uuid: payload.uuid,

    owner_user_id:
      ownerUserId,

    payload,

    created_at:
      new Date().toISOString(),

    attempts: 0,

    last_error: null,
  })
}


export async function
removePendingSurvey(
  uuid: string,
): Promise<void> {
  await db.pendingSurveys.delete(
    uuid,
  )
}


export async function
syncQueuedSurvey(
  payload: SurveySyncPayload,
): Promise<SurveySyncResponse> {
  try {
    const result =
      await syncSurvey(payload)

    await removePendingSurvey(
      payload.uuid,
    )

    return result
  } catch (error) {
    const pending =
      await db.pendingSurveys.get(
        payload.uuid,
      )

    if (pending) {
      await db.pendingSurveys.update(
        payload.uuid,
        {
          attempts:
            pending.attempts + 1,

          last_error:
            getErrorMessage(
              error,
            ),
        },
      )
    }

    throw error
  }
}


export async function
syncPendingSurveys():
Promise<number> {
  if (
    isSyncing ||
    !navigator.onLine
  ) {
    return 0
  }

  const ownerUserId =
    getSessionUserId()

  if (!ownerUserId) {
    return 0
  }

  isSyncing = true

  let synchronized = 0

  try {
    const pending =
      await db.pendingSurveys
        .where(
          'owner_user_id',
        )
        .equals(
          ownerUserId,
        )
        .sortBy(
          'created_at',
        )

    for (
      const item of pending
    ) {
      try {
        await syncSurvey(
          item.payload,
        )

        await db.pendingSurveys
          .delete(
            item.uuid,
          )

        synchronized += 1
      } catch (error) {
        await db.pendingSurveys
          .update(
            item.uuid,
            {
              attempts:
                item.attempts + 1,

              last_error:
                getErrorMessage(
                  error,
                ),
            },
          )

        if (
          !navigator.onLine
        ) {
          break
        }

        if (
          axios.isAxiosError(
            error,
          ) &&
          !error.response
        ) {
          break
        }

        if (
          axios.isAxiosError(
            error,
          ) &&
          error.response
            ?.status === 401
        ) {
          break
        }
      }
    }
  } finally {
    isSyncing = false
  }

  return synchronized
}