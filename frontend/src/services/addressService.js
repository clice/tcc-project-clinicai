/**
 * Serviço de consulta de endereço por CEP.
 *
 * Usa a API pública ViaCEP para preencher endereço automaticamente.
 */

import { onlyNumbers } from 'src/utils/formatters'

export const addressService = {
  /**
   * Busca endereço pelo CEP informado.
   */
  getAddressByZipCode: async (zipCode) => {
    const cleanedZipCode = onlyNumbers(zipCode)

    if (!cleanedZipCode || cleanedZipCode.length !== 8) {
      return null
    }

    const response = await fetch(`https://viacep.com.br/ws/${cleanedZipCode}/json/`)
    const data = await response.json()

    if (data.erro) {
      return null
    }

    return {
      zip_code: data.cep,
      address: data.logradouro || '',
      complement: data.complemento || '',
      neighborhood: data.bairro || '',
      city: data.localidade || '',
      state: data.uf || '',
    }
  },
}
