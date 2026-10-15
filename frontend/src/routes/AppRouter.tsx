import type {
  ReactNode,
} from 'react'

import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import {
  hasValidSession,
} from '../api/auth'

import LoginPage from '../pages/LoginPage'
import ProjectsPage from '../pages/ProjectsPage'


interface ProtectedRouteProps {
  children: ReactNode
}


function ProtectedRoute({
  children,
}: ProtectedRouteProps) {
  if (!hasValidSession()) {
    return (
      <Navigate
        to="/login"
        replace
      />
    )
  }

  return children
}


function AppRouter() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />

      <Route
        path="/login"
        element={
          <LoginPage />
        }
      />

      <Route
        path="/projects"
        element={
          <ProtectedRoute>
            <ProjectsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
    </Routes>
  )
}


export default AppRouter