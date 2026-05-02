/**
 * Formulário do módulo de Users.
 *
 * Usado para:
 * - criar usuário;
 * - visualizar usuário;
 * - editar usuário.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CButtonGroup,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CRow,
} from '@coreui/react'

import { userService } from 'src/services/userService'
import { roleService } from 'src/services/roleService'
import { statusService } from 'src/services/statusService'
import { clinicService } from 'src/services/clinicService'

import { formatCpfBR, formatPhoneBR, onlyNumbers } from 'src/utils/formatters'

const emptyUser = {
  name: '',
  email: '',
  cpf: '',
  phone: '',
  role_id: '',
  status_id: '',
  clinic_id: '',
  password: '',
  confirmPassword: '',
}

const UserForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyUser)
  const [roles, setRoles] = useState([])
  const [statuses, setStatuses] = useState([])
  const [clinics, setClinics] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const selectedRole = useMemo(
    () => roles.find((role) => String(role.id) === String(form.role_id)),
    [roles, form.role_id],
  )

  const requiresClinic = useMemo(() => {
    return selectedRole?.name && selectedRole.name !== 'admin_master'
  }, [selectedRole])

  const userStatuses = useMemo(() => {
    return statuses.filter((status) => status.applies_to === 'user')
  }, [statuses])

  const availableClinics = useMemo(() => {
    const selectedClinicId = String(form.clinic_id)

    return clinics.filter((clinic) => {
      const isActive = clinic.status_name === 'active'
      const isSelected = String(clinic.id) === selectedClinicId

      return isActive || isSelected
    })
  }, [clinics, form.clinic_id])

  const sortedRoles = useMemo(() => {
    return [...roles].sort((a, b) =>
      (a.display_name || a.name || '').localeCompare(b.display_name || b.name || '', 'pt-BR', {
        sensitivity: 'base',
      }),
    )
  }, [roles])

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Usuário'
    if (isEditMode) return 'Editar Usuário'
    return 'Detalhes do Usuário'
  }, [isCreateMode, isEditMode])

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        setError('')
        setSuccess('')

        const [rolesData, statusesData, clinicsData, userData] = await Promise.all([
          roleService.list(),
          statusService.list(),
          clinicService.list({ includeInactive: true }),
          isCreateMode ? Promise.resolve(null) : userService.getById(id),
        ])

        const loadedRoles = Array.isArray(rolesData) ? rolesData : []
        const loadedStatuses = Array.isArray(statusesData) ? statusesData : []
        const loadedClinics = Array.isArray(clinicsData) ? clinicsData : []

        setRoles(loadedRoles)
        setStatuses(loadedStatuses)
        setClinics(loadedClinics)

        if (userData) {
          setForm({
            name: userData.name ?? '',
            email: userData.email ?? '',
            cpf: formatCpfBR(userData.cpf ?? ''),
            phone: formatPhoneBR(userData.phone ?? ''),
            role_id: userData.role_id ? String(userData.role_id) : '',
            status_id: userData.status_id ? String(userData.status_id) : '',
            clinic_id: userData.clinic_id ? String(userData.clinic_id) : '',
            password: '',
            confirmPassword: '',
          })

          return
        }

        const activeUserStatus = loadedStatuses.find(
          (status) => status.name === 'active' && status.applies_to === 'user',
        )

        setForm({
          ...emptyUser,
          status_id: activeUserStatus ? String(activeUserStatus.id) : '',
        })
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Erro ao carregar os dados do usuário.')
      } finally {
        setIsLoading(false)
      }
    }

    void loadData()
  }, [id, isCreateMode])

  /**
   * Atualiza um campo do formulário.
   */
  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleRoleChange = (value) => {
    const role = roles.find((item) => String(item.id) === String(value))
    const nextRequiresClinic = role?.name && role.name !== 'admin_master'

    setForm((current) => ({
      ...current,
      role_id: value,
      clinic_id: nextRequiresClinic ? current.clinic_id : '',
    }))
  }

  /**
   * Valida os campos do formulário antes de enviar para a API.
   */
  const validateForm = () => {
    const cpfNumbers = onlyNumbers(form.cpf)

    if (!form.name.trim()) {
      setError('Informe o nome do usuário.')
      return false
    }

    if (!form.email.trim()) {
      setError('Informe o e-mail do usuário.')
      return false
    }

    if (cpfNumbers && cpfNumbers.length !== 11) {
      setError('CPF deve conter 11 números.')
      return false
    }

    if (!form.role_id || !form.status_id) {
      setError('Preencha o perfil de acesso e o status.')
      return false
    }

    if (requiresClinic && !form.clinic_id) {
      setError('Usuários que não são admin master devem estar vinculados a uma clínica.')
      return false
    }

    if (isCreateMode && !form.password.trim()) {
      setError('Informe a senha do usuário.')
      return false
    }

    if ((isCreateMode || form.password || form.confirmPassword) && form.password.trim().length < 6) {
      setError('A senha deve ter no mínimo 6 caracteres.')
      return false
    }

    if ((isCreateMode || form.password || form.confirmPassword) && form.password !== form.confirmPassword) {
      setError('Senha e confirmação de senha não coincidem.')
      return false
    }

    return true
  }

  /**
   * Monta o payload enviado para a API.
   */
  const buildUserPayload = () => {
    return {
      name: form.name.trim(),
      email: form.email.trim().toLowerCase(),
      cpf: onlyNumbers(form.cpf) || null,
      phone: onlyNumbers(form.phone) || null,
      role_id: Number(form.role_id),
      status_id: Number(form.status_id),
      clinic_id: requiresClinic ? Number(form.clinic_id) : null,
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    setError('')
    setSuccess('')

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        await userService.create({
          ...buildUserPayload(),
          password: form.password.trim(),
        })

        navigate('/users')
        return
      }

      if (isEditMode) {
        await userService.update(id, buildUserPayload())

        if (form.password.trim()) {
          await userService.updatePassword(id, form.password.trim())
        }

        setSuccess('Usuário atualizado com sucesso.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erro ao salvar o usuário.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Controle de Acesso</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            Gerencie os dados cadastrais e o perfil de acesso do usuário.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/users">
            Voltar
          </CButton>
        </div>
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados do usuário</strong>
        </CCardHeader>

        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}
          {success && <CAlert color="success">{success}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando usuário...</p>
          ) : (
            <CForm onSubmit={handleSubmit}>
              <CRow className="g-3">
                <CCol md={6}>
                  <CFormLabel>Nome</CFormLabel>
                  <CFormInput
                    value={form.name}
                    disabled={isReadOnly}
                    onChange={(event) => updateField('name', event.target.value)}
                    required
                  />
                </CCol>

                <CCol md={6}>
                  <CFormLabel>E-mail</CFormLabel>
                  <CFormInput
                    type="email"
                    value={form.email}
                    disabled={isReadOnly}
                    onChange={(event) => updateField('email', event.target.value)}
                    required
                  />
                </CCol>

                <CCol md={4}>
                  <CFormLabel>CPF</CFormLabel>
                  <CFormInput
                    value={form.cpf}
                    disabled={isReadOnly}
                    onChange={(event) => updateField('cpf', formatCpfBR(event.target.value))}
                    placeholder="000.000.000-00"
                  />
                </CCol>

                <CCol md={4}>
                  <CFormLabel>Telefone</CFormLabel>
                  <CFormInput
                    value={form.phone}
                    disabled={isReadOnly}
                    onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                    placeholder="(88) 99999-9999"
                  />
                </CCol>

                <CCol md={4}>
                  <CFormLabel>Status</CFormLabel>
                  <CFormSelect
                    value={form.status_id}
                    disabled={isReadOnly || isCreateMode}
                    onChange={(event) => updateField('status_id', event.target.value)}
                    required
                  >
                    <option value="">Selecione...</option>

                    {userStatuses.map((status) => (
                      <option key={status.id} value={status.id}>
                        {status.display_name || status.name}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Perfil de acesso</CFormLabel>
                  <CFormSelect
                    value={form.role_id}
                    disabled={isReadOnly}
                    onChange={(event) => handleRoleChange(event.target.value)}
                    required
                  >
                    <option value="">Selecione...</option>

                    {sortedRoles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.display_name || role.name}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Clínica</CFormLabel>
                  <CFormSelect
                    value={form.clinic_id}
                    disabled={isReadOnly || !requiresClinic}
                    onChange={(event) => updateField('clinic_id', event.target.value)}
                    required={requiresClinic}
                  >
                    <option value="">
                      {requiresClinic ? 'Selecione...' : ''}
                    </option>

                    {availableClinics.map((clinic) => (
                      <option key={clinic.id} value={clinic.id}>
                        {clinic.name}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>

                {!isReadOnly && (
                  <>
                    <CCol md={6}>
                      <CFormLabel>{isCreateMode ? 'Senha' : 'Nova senha'}</CFormLabel>
                      <CFormInput
                        type="password"
                        value={form.password}
                        autoComplete="new-password"
                        onChange={(event) => updateField('password', event.target.value)}
                        required={isCreateMode}
                        placeholder={isEditMode ? 'Preencha apenas se quiser alterar' : ''}
                      />
                    </CCol>

                    <CCol md={6}>
                      <CFormLabel>
                        {isCreateMode ? 'Confirmar senha' : 'Confirmar nova senha'}
                      </CFormLabel>
                      <CFormInput
                        type="password"
                        value={form.confirmPassword}
                        autoComplete="new-password"
                        onChange={(event) => updateField('confirmPassword', event.target.value)}
                        required={isCreateMode}
                        placeholder={isEditMode ? 'Preencha apenas se quiser alterar' : ''}
                      />
                    </CCol>
                  </>
                )}

                <CCol xs={12}>
                  <div className="border rounded p-3 bg-body-tertiary">
                    <div className="fw-semibold mb-1">Permissões do usuário</div>
                    <div className="text-body-secondary small">
                      As permissões são definidas automaticamente pelo perfil de acesso selecionado.
                    </div>
                  </div>
                </CCol>
              </CRow>

              {!isReadOnly && (
                <CButtonGroup className="mt-4">
                  <CButton color="primary" type="submit" disabled={isSaving}>
                    {isSaving ? 'Salvando...' : 'Salvar'}
                  </CButton>

                  <CButton color="secondary" variant="outline" as={Link} to="/users">
                    Cancelar
                  </CButton>
                </CButtonGroup>
              )}
            </CForm>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default UserForm