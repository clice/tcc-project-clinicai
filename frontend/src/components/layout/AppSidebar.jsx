/**
 * AppSidebar Component
 *
 * Barra lateral principal do sistema.
 *
 * Renderiza o menu configurado em src/_nav.jsx.
 */

import React, { useMemo } from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { CCloseButton, CSidebar, CSidebarBrand, CSidebarHeader } from '@coreui/react'
import CIcon from '@coreui/icons-react'

import { AppSidebarNav } from 'src/components/navigation/AppSidebarNav'
import { useAuth } from 'src/hooks/useAuth'
import { useExamStatusCounts } from 'src/hooks/useExamStatusCounts'

import { logo } from 'src/assets/brand/logo'
import { sygnet } from 'src/assets/brand/sygnet'

import { statusColors } from 'src/utils/constants'

import navigation from 'src/_nav'

const filterNavigationByRole = (items, roleName) => {
  return items
    .map((item) => {
      const allowedByRole = !item.roles || item.roles.includes(roleName)

      if (!allowedByRole) {
        return null
      }

      if (item.items) {
        const filteredItems = filterNavigationByRole(item.items, roleName)

        if (filteredItems.length === 0) {
          return null
        }

        return {
          ...item,
          items: filteredItems,
        }
      }

      return item
    })
    .filter(Boolean)
}

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
  const { roleName } = useAuth()
  const { counts: examCounts } = useExamStatusCounts()

  const unfoldable = useSelector((state) => state.sidebarUnfoldable)
  const sidebarShow = useSelector((state) => state.sidebarShow)

  const filteredNavigation = useMemo(() => {
    const roleFiltered = filterNavigationByRole(navigation, roleName)
    return injectCountBadges(roleFiltered, examCounts)
  }, [roleName, examCounts])

  return (
    <CSidebar
      className="border-end"
      colorScheme="dark"
      position="fixed"
      unfoldable={unfoldable}
      visible={sidebarShow}
      onVisibleChange={(visible) => {
        dispatch({ type: 'set', sidebarShow: visible })
      }}
    >
      <CSidebarHeader className="border-bottom">
        <CSidebarBrand to="/dashboard">
          <CIcon customClassName="sidebar-brand-full" icon={logo} height={32} />
          <CIcon customClassName="sidebar-brand-narrow" icon={sygnet} height={32} />
        </CSidebarBrand>

        <CCloseButton
          className="d-lg-none"
          dark
          onClick={() => dispatch({ type: 'set', sidebarShow: false })}
        />
      </CSidebarHeader>

      <AppSidebarNav items={filteredNavigation} />
    </CSidebar>
  )
}

export default React.memo(AppSidebar)