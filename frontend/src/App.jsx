/**
 * 
 */

import React, { Suspense, useEffect } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useSelector } from 'react-redux'

import { CSpinner, useColorModes } from '@coreui/react'

import 'src/scss/style.scss'
import 'src/scss/examples.scss'

// Provider
import { AuthProvider } from 'src/context/AuthContext'

// Routes
import PrivateRoute from 'src/components/auth/PrivateRoute'
import PublicRoute from 'src/components/auth/PublicRoute'

// Containers
const DefaultLayout = React.lazy(() => import('src/layout/DefaultLayout'))

// Pages
const Login = React.lazy(() => import('src/views/auth/Login'))
const Error404 = React.lazy(() => import('src/views/errors/Error404'))
const Error500 = React.lazy(() => import('src/views/errors/Error500'))

const App = () => {
  const { isColorModeSet, setColorMode } = useColorModes('clinicai-theme')
  const storedTheme = useSelector((state) => state.theme)

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.href.split('?')[1])
    const theme = urlParams.get('theme') && urlParams.get('theme').match(/^[A-Za-z0-9\s]+/)[0]

    if (theme) {
      setColorMode(theme)
    }

    if (isColorModeSet()) {
      return
    }

    setColorMode(storedTheme)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AuthProvider>
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
              exact path="/login" 
              name="Login" 
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>              
              } 
            />

            {/* Errors */}
            <Route 
              exact path="/404" 
              name="Erro 404" 
              element={
                <Error404 />
              } 
            />
            <Route 
              exact path="/500" 
              name="Erro 500" 
              element={
                <Error500 />
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
    </AuthProvider>
  )
}

export default App
