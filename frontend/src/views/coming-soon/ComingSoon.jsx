/**
 * Página temporária para módulos ainda não implementados.
 *
 * Usada para permitir que o menu já exista sem quebrar a navegação.
 */

import React from 'react'
import { CCard, CCardBody, CCardTitle, CCardText } from '@coreui/react'

const ComingSoon = () => {
  return (
    <CCard>
      <CCardBody>
        <CCardTitle>Módulo em desenvolvimento</CCardTitle>
        <CCardText>
          Esta área já faz parte do planejamento do ClinicAI, mas ainda será implementada nas
          próximas etapas.
        </CCardText>
      </CCardBody>
    </CCard>
  )
}

export default ComingSoon
