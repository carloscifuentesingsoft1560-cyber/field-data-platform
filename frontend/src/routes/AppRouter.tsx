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

import AdminProjectsPage from '../pages/AdminProjectsPage'
import DynamicFormPage from '../pages/DynamicFormPage'
import LoginPage from '../pages/LoginPage'
import ProjectFormsPage from '../pages/ProjectFormsPage'
import ProjectsPage from '../pages/ProjectsPage'
import SurveyDetailPage from '../pages/SurveyDetailPage'
import SurveysPage from '../pages/SurveysPage'


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
        path="/admin/projects"
        element={
          <ProtectedRoute>
            <AdminProjectsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/projects/:projectId"
        element={
          <ProtectedRoute>
            <ProjectFormsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/projects/:projectId/surveys"
        element={
          <ProtectedRoute>
            <SurveysPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/projects/:projectId/surveys/:surveyId"
        element={
          <ProtectedRoute>
            <SurveyDetailPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/projects/:projectId/forms/:formId"
        element={
          <ProtectedRoute>
            <DynamicFormPage />
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