/**
 * Rodapé padrão da aplicação.
 *
 * Exibe informações básicas do sistema.
 */

import React from 'react'
import { CFooter } from '@coreui/react'

const AppFooter = () => {
  return (
    <CFooter className="px-4">
      <div>
        <span className="ms-1">ClinicAI &copy; 2026</span>
      </div>
    </CFooter>
  )
}

export default React.memo(AppFooter)