import {
  useEffect,
} from 'react'

import {
  useLocation,
} from 'react-router-dom'

import {
  hasValidSession,
} from '../api/auth'

import {
  syncPendingSurveys,
} from '../services/surveyQueue'


function SyncManager() {
  const location =
    useLocation()


  useEffect(() => {
    if (
      navigator.onLine &&
      hasValidSession()
    ) {
      void syncPendingSurveys()
        .catch(() => {
          // La encuesta permanece
          // almacenada localmente.
        })
    }
  }, [
    location.pathname,
  ])


  useEffect(() => {
    const handleOnline = () => {
      if (
        hasValidSession()
      ) {
        void syncPendingSurveys()
          .catch(() => {
            // Se intentará nuevamente.
          })
      }
    }

    window.addEventListener(
      'online',
      handleOnline,
    )

    return () => {
      window.removeEventListener(
        'online',
        handleOnline,
      )
    }
  }, [])


  return null
}


export default SyncManager