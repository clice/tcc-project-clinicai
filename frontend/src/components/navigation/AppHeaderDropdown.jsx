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
      <CDropdownToggle
        placement="bottom-end"
        className="d-flex align-items-center gap-2 py-0 pe-0 text-decoration-none"
        caret={false}
        aria-label={`Abrir menu do usuário ${user?.name || 'Usuário'}`}
      >
        <span
          className="clinicai-user-greeting d-none d-sm-inline"
          title={`Olá, ${user?.name || 'Usuário'}`}
        >
          Olá, {user?.name || 'Usuário'}
        </span>

        <span className="clinicai-user-divider d-none d-sm-block" aria-hidden="true" />

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
        <CDropdownHeader className="clinicai-user-menu-header fw-semibold mb-2">
          Usuário
        </CDropdownHeader>

        <CDropdownItem as="div" className="d-flex flex-column align-items-start">
          <strong className="clinicai-page-title">{user?.name || 'Usuário'}</strong>
          <small className="text-body-secondary">{user?.email}</small>
          <small className="text-body-secondary">
            {user?.role_display_name || user?.role_name}
          </small>
        </CDropdownItem>

        <CDropdownDivider />

        <CDropdownItem
          as="button"
          type="button"
          className="clinicai-user-menu-action"
          onClick={() => navigate('/profile')}
        >
          <CIcon icon={cilUser} className="me-2" />
          Perfil
        </CDropdownItem>

        <CDropdownDivider />

        <CDropdownItem
          as="button"
          type="button"
          className="clinicai-user-menu-action"
          onClick={handleLogout}
        >
          <CIcon icon={cilAccountLogout} className="me-2" />
          Sair
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown
