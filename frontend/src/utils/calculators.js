/**
 * Funções utilitárias de calculos.
 */

/**
 * Calcula a idade baseado na data de nascimento e ano atual.
 */
export const calculateAge = (birthDate) => {
  if (!birthDate) return '-'

  const date = new Date(birthDate)

  if (Number.isNaN(date.getTime())) return '-'

  const today = new Date()
  let age = today.getFullYear() - date.getFullYear()
  const monthDifference = today.getMonth() - date.getMonth()

  if (
    monthDifference < 0 ||
    (monthDifference === 0 && today.getDate() < date.getDate())
  ) {
    age -= 1
  }

  return age
}