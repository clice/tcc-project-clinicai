/**
 * Componente genérico de abas com contador.
 *
 * Pode ser usado em listagens para separar registros por status,
 * por exemplo:
 * - clínicas ativas;
 * - clínicas inativas.
 */

import React from 'react'
import { CBadge, CNav, CNavItem, CNavLink } from '@coreui/react'

const AppTabs = ({ activeTab, counts = {}, onChange, tabs = [] }) => {
  return (
    <CNav variant="tabs" role="tablist" className="clinicai-tabs mb-3">
      {tabs.map((tab) => (
        <CNavItem key={tab.key}>
          <CNavLink
            active={activeTab === tab.key}
            component="button"
            type="button"
            role="tab"
            onClick={() => onChange(tab.key)}
          >
            {tab.label}

            <CBadge
              color="secondary"
              shape="rounded-pill"
              className={`ms-2 ${
                activeTab === tab.key
                  ? 'clinicai-tab-badge-active'
                  : 'clinicai-tab-badge-inactive'
              }`}
            >
              {counts[tab.key] ?? 0}
            </CBadge>
          </CNavLink>
        </CNavItem>
      ))}
    </CNav>
  )
}

export default AppTabs