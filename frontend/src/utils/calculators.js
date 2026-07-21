/**
 * Funções utilitárias de calculos.
 */

const parseCalendarDate = (value) => {
  if (!value) return null

  if (value instanceof Date) {
    if (Number.isNaN(value.getTime())) return null

    return new Date(value.getFullYear(), value.getMonth(), value.getDate())
  }

  const stringValue = String(value)
  const dateOnlyMatch = stringValue.match(/^(\d{4})-(\d{2})-(\d{2})$/)

  if (dateOnlyMatch) {
    const [, yearText, monthText, dayText] = dateOnlyMatch
    const year = Number(yearText)
    const month = Number(monthText) - 1
    const day = Number(dayText)
    const date = new Date(year, month, day)

    if (date.getFullYear() !== year || date.getMonth() !== month || date.getDate() !== day) {
      return null
    }

    return date
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return null

  return date
}

/**
 * Calcula a idade na data de referência informada.
 *
 * Quando a referência não é fornecida, mantém o comportamento
 * de calcular a idade atual.
 */
export const calculateAge = (birthDate, referenceDate = new Date()) => {
  const birth = parseCalendarDate(birthDate)
  const reference = parseCalendarDate(referenceDate)

  if (!birth || !reference || birth > reference) {
    return '-'
  }

  let age = reference.getFullYear() - birth.getFullYear()
  const monthDifference = reference.getMonth() - birth.getMonth()

  if (monthDifference < 0 || (monthDifference === 0 && reference.getDate() < birth.getDate())) {
    age -= 1
  }

  return age
}
