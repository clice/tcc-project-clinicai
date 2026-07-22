/**
 * AppSidebar Component
 *
 * Barra lateral principal do sistema.
 *
 * Renderiza o menu configurado em src/_nav.jsx.
 */

import React, { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'

import { CCloseButton, CSidebar, CSidebarBrand, CSidebarHeader } from '@coreui/react'
import CIcon from '@coreui/icons-react'

import { AppSidebarNav } from 'src/components/navigation/AppSidebarNav'
import { useAuth } from 'src/hooks/useAuth'
import { useExamStatusCounts } from 'src/hooks/useExamStatusCounts'

import { clinicaiSygnet } from 'src/assets/brand/clinicaiSygnet'

import { statusColors } from 'src/utils/constants'
import { filterNavigationByAccess } from 'src/utils/navigationAccess.mjs'
import { hasPermission, PERMISSIONS } from 'src/utils/permissions'

import navigation from 'src/_nav'

// Preenche o badge de qualquer item que declare `badgeKey` (hoje, os
// status de exame no submenu) com a contagem real vinda do backend.
// Itens sem `badgeKey` (ou sem contagem disponível ainda) não são
// alterados — mantêm o badge estático que já tivessem, se houver.
const injectCountBadges = (items, counts) => {
  return items.map((item) => {
    if (item.items) {
      return { ...item, items: injectCountBadges(item.items, counts) }
    }

    if (item.badgeKey && counts[item.badgeKey] !== undefined) {
      return {
        ...item,
        badge: {
          color: statusColors[item.badgeKey] || 'secondary',
          text: String(counts[item.badgeKey]),
        },
      }
    }

    return item
  })
}

const AppSidebar = () => {
  const dispatch = useDispatch()
  const { roleName, user } = useAuth()
  const canListExams = hasPermission(user, PERMISSIONS.EXAMS_LIST)
  const { counts: examCounts } = useExamStatusCounts({}, canListExams)

  const unfoldable = useSelector((state) => state.sidebarUnfoldable)
  const sidebarShow = useSelector((state) => state.sidebarShow)

  const filteredNavigation = useMemo(() => {
    const accessibleNavigation = filterNavigationByAccess(navigation, {
      roleName,
      hasPermission: (permission) => hasPermission(user, permission),
    })
    return injectCountBadges(accessibleNavigation, examCounts)
  }, [roleName, user, examCounts])

  return (
    <CSidebar
      className="app-sidebar border-end"
      colorScheme="dark"
      position="fixed"
      unfoldable={unfoldable}
      visible={sidebarShow}
      onVisibleChange={(visible) => {
        dispatch({ type: 'set', sidebarShow: visible })
      }}
    >
      <CSidebarHeader className="clinicai-sidebar-header">
        <CSidebarBrand
          as={Link}
          className="clinicai-sidebar-brand"
          to="/dashboard"
          aria-label="Ir para o Dashboard"
          title="Dashboard"
        >
          <span className="sidebar-brand-full clinicai-brand-full">
            <CIcon customClassName="clinicai-brand-icon" icon={clinicaiSygnet} height={42} />
            <span className="clinicai-brand-name">
              Clinic<span className="clinicai-brand-ai">AI</span>
            </span>
          </span>
          <CIcon
            customClassName="sidebar-brand-narrow clinicai-brand-icon"
            icon={clinicaiSygnet}
            height={38}
          />
        </CSidebarBrand>

        <CCloseButton
          className="d-lg-none"
          dark
          onClick={() => dispatch({ type: 'set', sidebarShow: false })}
        />
      </CSidebarHeader>

      <AppSidebarNav items={filteredNavigation} roleName={roleName} />
    </CSidebar>
  )
}

export default React.memo(AppSidebar)
