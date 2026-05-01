/**
 * AppSidebar Component
 *
 * Barra lateral principal do sistema.
 *
 * Renderiza o menu configurado em src/_nav.jsx.
 */

import React from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { CCloseButton, CSidebar, CSidebarBrand, CSidebarHeader } from '@coreui/react'
import CIcon from '@coreui/icons-react'

import { AppSidebarNav } from 'src/components/navigation/AppSidebarNav'

import { logo } from 'src/assets/brand/logo'
import { sygnet } from 'src/assets/brand/sygnet'

import navigation from 'src/_nav'

const AppSidebar = () => {
  const dispatch = useDispatch()

  const unfoldable = useSelector((state) => state.sidebarUnfoldable)
  const sidebarShow = useSelector((state) => state.sidebarShow)

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

      <AppSidebarNav items={navigation} />
    </CSidebar>
  )
}

export default React.memo(AppSidebar)