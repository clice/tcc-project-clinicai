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

import { logo } from 'src/assets/brand/logo'
import { sygnet } from 'src/assets/brand/sygnet'

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

const AppSidebar = () => {
  const dispatch = useDispatch()
  const { roleName } = useAuth()

  const unfoldable = useSelector((state) => state.sidebarUnfoldable)
  const sidebarShow = useSelector((state) => state.sidebarShow)

  const filteredNavigation = useMemo(() => {
    return filterNavigationByRole(navigation, roleName)
  }, [roleName])

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