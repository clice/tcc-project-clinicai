/**
 * Filtra a configuração da navegação com as mesmas regras usadas nas rotas.
 *
 * A função é independente de React/CoreUI para permitir teste direto. Os
 * metadados `roles` e `permission` são consumidos aqui e removidos antes de o
 * item ser entregue ao componente visual, evitando repassá-los ao DOM.
 */
export const filterNavigationByAccess = (items, { roleName, hasPermission = () => false }) => {
  return items
    .map((item) => {
      // Mesma precedência de RoleRoute: uma permissão declarada é a fonte da
      // verdade; roles funcionam como regra exclusiva ou fallback.
      const allowed = item.permission
        ? hasPermission(item.permission)
        : !item.roles || item.roles.includes(roleName)

      if (!allowed) {
        return null
      }

      const { roles, permission, ...visibleItem } = item

      if (item.items) {
        const filteredItems = filterNavigationByAccess(item.items, {
          roleName,
          hasPermission,
        })

        // Um grupo sem nenhuma opção acessível não deve aparecer vazio.
        if (filteredItems.length === 0) {
          return null
        }

        return {
          ...visibleItem,
          items: filteredItems,
        }
      }

      return visibleItem
    })
    .filter(Boolean)
}
