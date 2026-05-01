/**
 * Menu do usuário autenticado no cabeçalho.
 *
 * Exibe dados básicos do usuário logado e permite encerrar sessão.
 */

import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CAvatar,
  CBadge,
  CDropdown,
  CDropdownDivider,
  CDropdownHeader,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
} from '@coreui/react'
import {
  cilAccountLogout,
  cilBell,
  cilCreditCard,
  cilCommentSquare,
  cilEnvelopeOpen,
  cilFile,
  cilLockLocked,
  cilSettings,
  cilTask,
  cilUser,
} from '@coreui/icons'
import CIcon from '@coreui/icons-react'

import avatar8 from 'src/assets/images/avatars/8.jpg'

const AppHeaderDropdown = () => {

  return (
    <CDropdown variant="nav-item">
      <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
        <CAvatar src={avatar8} size="md" />
      </CDropdownToggle>

      <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">
          Usuário
        </CDropdownHeader>

        <CDropdownDivider />

        <CDropdownItem href="#">
          <CIcon icon={cilUser} className="me-2" />
          Perfil
        </CDropdownItem>

        <CDropdownDivider />

        <CDropdownItem as="button" type="button">
          <CIcon icon={cilAccountLogout} className="me-2" />
          Sair
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown