/**
 * Funções utilitárias de formatação.
 * 
 * Usadas para:
 * - limpar máscaras antes de enviar dados ao backend;
 * - exibir CNPJ, telefone e CEP no padrão brasileiro;
 * - manter os formulários mais legíveis.
 */

/**
 * Remove tudo que não for número.
 */
export const onlyNumbers = (value = '') => {
  return String(value).replace(/\D/g, '')
  
}

/**
 * Formata CPF:
 * 00000000000 -> 000.000.000-00
 */
export const formatCpfBR = (value = '') => {
  const numbers = onlyNumbers(value).slice(0, 11)

  return numbers
    .replace(/^(\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1-$2')
}

/**
 * Formata CNPJ:
 * 00000000000000 -> 00.000.000/0000-00
 */
export const formatCnpjBR = (value = '') => {
  const numbers = onlyNumbers(value).slice(0, 14)

  return numbers
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}

/**
 * Formata Data:
 * YYYY-MM-DD HH:MM:SS -> DD/MM/YYYY às HH:MM
 */
export const formatDateTimeBR = (value) => {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '-'

  return `${date.toLocaleDateString('pt-BR')} às ${date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

/**
 * Formata telefone fixo ou celular:
 * 88999998888 -> (88) 99999-8888
 * 8833334444  -> (88) 3333-4444
 */
export const formatPhoneBR = (value = '') => {
  const numbers = onlyNumbers(value).slice(0, 11)

  if (numbers.length <= 10) {
    return numbers
      .replace(/^(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2')
  }

  return numbers
    .replace(/^(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
}

/**
 * Formata CEP:
 * 63000000 -> 63000-000
 */
export const formatZipCodeBR = (value = '') => {
  const numbers = onlyNumbers(value).slice(0, 8)

  return numbers.replace(/^(\d{5})(\d)/, '$1-$2')
}

/**
 * Formata Sexo:
 */
export const formatSex = (value) => {
  const labels = {
    female: 'Feminino',
    male: 'Masculino',
    other: 'Outro',
  }

  return labels[value] || '-'
}