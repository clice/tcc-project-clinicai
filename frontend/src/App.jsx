/**
 *
 */

import React, { Suspense, useEffect } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { CSpinner } from '@coreui/react'

import 'src/scss/style.scss'

// Provider
import { AuthProvider } from 'src/contexts/AuthContext'
import { FeedbackProvider } from 'src/contexts/FeedbackContext'

// Routes
import PrivateRoute from 'src/components/auth/PrivateRoute'
import PublicRoute from 'src/components/auth/PublicRoute'

// Containers
const DefaultLayout = React.lazy(() => import('src/layout/DefaultLayout'))

// Pages
const Login = React.lazy(() => import('src/views/auth/Login'))

const App = () => {
  useEffect(() => {
    document.documentElement.setAttribute('data-coreui-theme', 'light')
    localStorage.removeItem('clinicai-theme')
  }, [])

  return (
    <AuthProvider>
      <FeedbackProvider>
        <HashRouter>
          <Suspense
            fallback={
              <div className="pt-3 text-center">
                <CSpinner color="primary" variant="grow" />
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Navigate to="/login" replace />} />

              {/* Login */}
              <Route
                exact
                path="/login"
                name="Login"
                element={
                  <PublicRoute>
                    <Login />
                  </PublicRoute>
                }
              />

              {/* Layout */}
              <Route
                path="/*"
                name="Home"
                element={
                  <PrivateRoute>
                    <DefaultLayout />
                  </PrivateRoute>
                }
              />
            </Routes>
          </Suspense>
        </HashRouter>
      </FeedbackProvider>
    </AuthProvider>
  )
}

export default App
