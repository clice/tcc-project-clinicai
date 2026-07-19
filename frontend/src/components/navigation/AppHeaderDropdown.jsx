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

import { useAuth } from 'src/hooks/useAuth'
import { getStoredUser } from 'src/utils/token'

const AppHeaderDropdown = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <CDropdown variant="nav-item">
      <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
        <CAvatar
          className="clinicai-user-avatar"
          color="primary"
          textColor="white"
          size="md"
        >
          <CIcon icon={cilUser} />
        </CAvatar>
      </CDropdownToggle>

      <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">
          Usuário
        </CDropdownHeader>

        <CDropdownItem as="div" className="d-flex flex-column align-items-start">
          <strong>{user?.name || 'Usuário'}</strong>
          <small className="text-body-secondary">{user?.email}</small>
          <small className="text-body-secondary">
            {user?.role_display_name || user?.role_name}
          </small>
        </CDropdownItem>

        <CDropdownDivider />

        <CDropdownItem as="button" type="button" onClick={() => navigate('/profile')}>
          <CIcon icon={cilUser} className="me-2" />
          Perfil
        </CDropdownItem>

        <CDropdownDivider />

        <CDropdownItem as="button" type="button" onClick={handleLogout}>
          <CIcon icon={cilAccountLogout} className="me-2" />
          Sair
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown