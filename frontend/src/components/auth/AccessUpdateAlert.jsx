/**
 * Aviso global exibido quando a sessão detecta mudança de role ou permissões.
 */

import React from 'react'
import { CAlert, CContainer } from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'

const AccessUpdateAlert = () => {
  const { accessChangeNotice, dismissAccessChangeNotice } = useAuth()

  if (!accessChangeNotice) return null

  return (
    <CContainer className="px-4 pt-3" lg>
      <CAlert color="warning" className="mb-0" role="status">
        <div className="d-flex align-items-start justify-content-between gap-3">
          <div>
            <strong>Acessos atualizados</strong>
            <div>{accessChangeNotice.message}</div>
          </div>
          <button
            type="button"
            className="btn-close"
            aria-label="Fechar aviso de atualização de acessos"
            onClick={dismissAccessChangeNotice}
          />
        </div>
      </CAlert>
    </CContainer>
  )
}

export default AccessUpdateAlert
