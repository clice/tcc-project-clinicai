/**
 * Área principal de conteúdo da aplicação.
 *
 * Responsável por renderizar as rotas cadastradas no sistema.
 * Também exibe um carregamento enquanto páginas lazy-loaded
 * estão sendo importadas.
 */

import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { CContainer, CSpinner } from '@coreui/react'

import { routes } from 'src/routes'
import RoleRoute from 'src/components/auth/RoleRoute'

const AppContent = () => {
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
                    <RoleRoute allowedRoles={route.roles}>
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
