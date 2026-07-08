/**
 * Serviços do módulo Users.
 *
 * Centraliza as chamadas HTTP relacionadas aos usuários.
 */

import api from 'src/services/api'

export const userService = {
  /**
   * Lista usuários.
   */
  list: async ({
    search = '',
    clinicId = '',
    role = '',
    status = '',
  } = {}) => {
    const response = await api.get('/users/', {
      params: {
        search: search || undefined,
        clinic_id: clinicId || undefined,
        role: role || undefined,
        status: status || undefined,
      },
    })

    return response.data
  },

  /**
   * Busca um usuário pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/users/${id}`)
    return response.data
  },

  /**
   * Cria um novo usuário.
   */
  create: async (payload) => {
    const response = await api.post('/users/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente um usuário existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/users/${id}`, payload)
    return response.data
  },

  /**
   * Atualiza somente a senha do usuário.
   * currentPassword só é necessário quando o próprio usuário troca a
   * própria senha; um admin_master resetando a senha de outro usuário
   * pode omitir esse campo.
   */
  updatePassword: async (id, password, currentPassword) => {
    const response = await api.patch(`/users/${id}/password`, {
      password,
      current_password: currentPassword || undefined,
    })
    return response.data
  },

  /**
   * Atualiza a senha do próprio usuário autenticado (doctor, clinic_staff
   * ou admin_master), sempre exigindo a senha atual.
   */
  updateMyPassword: async (password, currentPassword) => {
    const response = await api.patch('/users/me/password', {
      password,
      current_password: currentPassword,
    })
    return response.data
  },

  /**
   * Inativa um usuário.
   */
  inactivate: async (id) => {
    const response = await api.patch(`/users/${id}/inactivate`)
    return response.data
  },

  /**
   * Ativa um usuário.
   */
  activate: async (id) => {
    const response = await api.patch(`/users/${id}/activate`)
    return response.data
  },

  /**
   * Lista médicos ativos de uma clínica.
   */
  listDoctorsByClinic: async (clinicId) => {
    const response = await api.get('/users/doctors', {
      params: {
        clinic_id: Number(clinicId),
      },
    })

    return Array.isArray(response.data) ? response.data : []
  }
}
