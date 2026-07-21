/**
 * Área principal de conteúdo da aplicação.
 *
 * Responsável por renderizar as rotas cadastradas no sistema.
 * Também exibe um carregamento enquanto páginas lazy-loaded
 * estão sendo importadas.
 */

import React, { Suspense, useEffect } from 'react'
import { matchPath, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { CContainer, CSpinner } from '@coreui/react'

import { routes } from 'src/routes'
import RoleRoute from 'src/components/auth/RoleRoute'

const AppContent = () => {
  const { pathname } = useLocation()

  useEffect(() => {
    const currentRoute = routes.find(
      (route) =>
        route.element &&
        matchPath(
          {
            path: route.path,
            end: true,
          },
          pathname,
        ),
    )

    document.title = currentRoute?.name ? `ClinicAI | ${currentRoute.name}` : 'ClinicAI'
  }, [pathname])

  return (
    <CContainer className="px-4" lg>
      <Suspense fallback={<CSpinner color="primary" />}>
        <Routes>
          {routes.map((route, idx) => {
            return (
              route.element && (
                <Route
                  key={idx}
                  path={route.path}
                  exact={route.exact}
                  name={route.name}
                  element={
                    <RoleRoute allowedRoles={route.roles} requiredPermission={route.permission}>
                      <route.element />
                    </RoleRoute>
                  }
                />
              )
            )
          })}

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </CContainer>
  )
}

export default React.memo(AppContent)
