import React from 'react'
import { NavLink } from 'react-router-dom'
import PropTypes from 'prop-types'

import SimpleBar from 'simplebar-react'
import 'simplebar-react/dist/simplebar.min.css'

import { CBadge, CNavLink, CSidebarNav } from '@coreui/react'

export const AppSidebarNav = ({
  items,
  roleName = null,
}) => {
  const navLink = (name, icon, badge, indent = false) => {
    return (
      <>
        {icon
          ? icon
          : indent && (
              <span className="nav-icon">
                <span className="nav-icon-bullet"></span>
              </span>
            )}
        {name && name}
        {badge && (
          <CBadge
            color={badge.color}
            className={`ms-auto ${
              badge.color === 'completed'
                ? 'clinicai-success-badge'
                : ''
            }`}
            size="sm"
          >
            {badge.text}
          </CBadge>
        )}
      </>
    )
  }

  const navItem = (item, index, indent = false) => {
    const { component, name, badge, icon, ...rest } = item
    const Component = component
    return (
      <Component as="div" key={index}>
        {rest.to || rest.href ? (
          <CNavLink
            {...(rest.to && { as: NavLink })}
            {...(rest.href && { target: '_blank', rel: 'noopener noreferrer' })}
            {...rest}
          >
            {navLink(name, icon, badge, indent)}
          </CNavLink>
        ) : (
          navLink(name, icon, badge, indent)
        )}
      </Component>
    )
  }

  const navGroup = (item, index) => {
    const {
      component,
      name,
      icon,
      items,
      to,
      lockedOpenRoles = [],
      ...rest
    } = item

    const Component = component

    const isLockedOpen =
      lockedOpenRoles.includes(
        roleName,
      )

    const groupProperties =
      isLockedOpen
        ? {
            ...rest,
            visible: true,
            onVisibleChange: () => {},
          }
        : rest

    return (
      <Component
        compact
        as="div"
        key={index}
        toggler={
          navLink(name, icon)
        }
        {...groupProperties}
      >
        {items?.map(
          (
            childItem,
            childIndex,
          ) =>
            childItem.items
              ? navGroup(
                  childItem,
                  childIndex,
                )
              : navItem(
                  childItem,
                  childIndex,
                  true,
                ),
        )}
      </Component>
    )
  }

  return (
    <CSidebarNav as={SimpleBar}>
      {items &&
        items.map((item, index) => (item.items ? navGroup(item, index) : navItem(item, index)))}
    </CSidebarNav>
  )
}

AppSidebarNav.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.any,
  ).isRequired,
  roleName: PropTypes.string,
}
