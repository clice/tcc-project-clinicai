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
  CBadge,
  CButton,
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

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { userService } from 'src/services/userService'
import { roleService } from 'src/services/roleService'
import { clinicService } from 'src/services/clinicService'
import { patientService } from 'src/services/patientService'
import { examService } from 'src/services/examService'

import { statusColors } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import { formatCpfBR, formatPhoneBR, onlyNumbers } from 'src/utils/formatters'
import { getUserRole, ROLES } from 'src/utils/permissions'

const emptyUser = {
  name: '',
  email: '',
  cpf: '',
  phone: '',
  crm_number: '',
  crm_uf: '',
  role_id: '',
  clinic_id: '',
  password: '',
  confirmPassword: '',
}

const brazilianStates = [
  'AC',
  'AL',
  'AP',
  'AM',
  'BA',
  'CE',
  'DF',
  'ES',
  'GO',
  'MA',
  'MT',
  'MS',
  'MG',
  'PA',
  'PB',
  'PR',
  'PE',
  'PI',
  'RJ',
  'RN',
  'RS',
  'RO',
  'RR',
  'SC',
  'SP',
  'SE',
  'TO',
]

const UserForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()
  const isClinicManager = getUserRole(currentUser) === ROLES.CLINIC_MANAGER

  const [form, setForm] = useState(emptyUser)
  const [roles, setRoles] = useState([])
  const [clinics, setClinics] = useState([])
  const [doctorPatients, setDoctorPatients] = useState([])
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'
  const isSelfRecord = !isCreateMode && String(currentUser?.id) === String(id)

  const selectedRole = useMemo(
    () => roles.find((role) => String(role.id) === String(form.role_id)),
    [roles, form.role_id],
  )

  const isDoctorRole = selectedRole?.name === ROLES.DOCTOR

  const requiresClinic = useMemo(() => {
    return selectedRole?.name && selectedRole.name !== ROLES.ADMIN_MASTER
  }, [selectedRole])

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
    const subject = isClinicManager ? 'Médico' : 'Usuário'

    if (isCreateMode) return `Cadastrar ${subject}`
    if (isEditMode) return `Editar ${subject}`
    return `Detalhes do ${subject}`
  }, [isClinicManager, isCreateMode, isEditMode])

  useEffect(() => {
    const loadData = async () => {
      try {
        startLoading()
        showError('')
        showSuccess('')

        let loadedRoles = []
        let loadedClinics = []
        let userData = null

        if (isClinicManager) {
          const [optionsData, loadedUser] = await Promise.all([
            userService.getDoctorManagementOptions(),
            isCreateMode ? Promise.resolve(null) : userService.getById(id),
          ])

          loadedRoles = optionsData?.role ? [optionsData.role] : []
          loadedClinics = optionsData?.clinic ? [optionsData.clinic] : []
          userData = loadedUser
        } else {
          const [rolesData, clinicsData, loadedUser] = await Promise.all([
            roleService.list(),
            clinicService.list({ includeInactive: true }),
            isCreateMode ? Promise.resolve(null) : userService.getById(id),
          ])

          loadedRoles = Array.isArray(rolesData) ? rolesData : []
          loadedClinics = Array.isArray(clinicsData) ? clinicsData : []
          userData = loadedUser
        }

        setRoles(loadedRoles)
        setClinics(loadedClinics)

        if (userData) {
          setForm({
            name: userData.name ?? '',
            email: userData.email ?? '',
            cpf: formatCpfBR(userData.cpf ?? ''),
            phone: formatPhoneBR(userData.phone ?? ''),
            crm_number: userData.crm_number ?? '',
            crm_uf: userData.crm_uf ?? '',
            role_id: userData.role_id ? String(userData.role_id) : '',
            clinic_id: userData.clinic_id ? String(userData.clinic_id) : '',
            password: '',
            confirmPassword: '',
          })

          return
        }

        setForm({
          ...emptyUser,
          role_id: isClinicManager && loadedRoles[0] ? String(loadedRoles[0].id) : '',
          clinic_id: isClinicManager && loadedClinics[0] ? String(loadedClinics[0].id) : '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar os dados do usuário.'))
      } finally {
        stopLoading()
      }
    }

    void loadData()
  }, [id, isClinicManager, isCreateMode, showError, showSuccess, startLoading, stopLoading])

  useEffect(() => {
    if (isCreateMode || !id || !isDoctorRole) {
      return undefined
    }

    let isCancelled = false

    const loadDoctorPatients = async () => {
      try {
        const [patientsData, examsData] = await Promise.all([
          patientService.list({
            doctorId: id,
            includeInactive: true,
          }),
          examService.list({
            doctorId: id,
            includeInactive: true,
          }),
        ])

        if (isCancelled) return

        const examsByPatient = (Array.isArray(examsData) ? examsData : []).reduce(
          (counts, exam) => {
            const patientId = String(exam.patient_id)
            counts[patientId] = (counts[patientId] || 0) + 1
            return counts
          },
          {},
        )

        setDoctorPatients(
          (Array.isArray(patientsData) ? patientsData : []).map((patient) => ({
            ...patient,
            exam_count: examsByPatient[String(patient.id)] || 0,
          })),
        )
      } catch (err) {
        if (!isCancelled) {
          setDoctorPatients([])
          showError(getErrorMessage(err, 'Não foi possível carregar os pacientes do médico.'))
        }
      }
    }

    void loadDoctorPatients()

    return () => {
      isCancelled = true
    }
  }, [id, isCreateMode, isDoctorRole, showError])

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
      crm_number: role?.name === ROLES.DOCTOR ? current.crm_number : '',
      crm_uf: role?.name === ROLES.DOCTOR ? current.crm_uf : '',
    }))
  }

  /**
   * Valida os campos do formulário antes de enviar para a API.
   */
  const validateForm = () => {
    const cpfNumbers = onlyNumbers(form.cpf)

    if (!form.name.trim()) {
      showError('Informe o nome do usuário.')
      return false
    }

    if (!form.email.trim()) {
      showError('Informe o e-mail do usuário.')
      return false
    }

    if (!cpfNumbers) {
      showError('Informe o CPF do usuário.')
      return false
    }

    if (cpfNumbers.length !== 11) {
      showError('CPF deve conter 11 números.')
      return false
    }

    if (!form.role_id) {
      showError('Preencha o perfil de acesso.')
      return false
    }

    if (requiresClinic && !form.clinic_id) {
      showError('Usuários que não são admin master devem estar vinculados a uma clínica.')
      return false
    }

    if (isDoctorRole && !form.crm_number.trim()) {
      showError('Informe o CRM do médico.')
      return false
    }

    if (isDoctorRole && !form.crm_uf) {
      showError('Selecione a UF do CRM.')
      return false
    }

    if (isCreateMode && !form.password.trim()) {
      showError('Informe a senha do usuário.')
      return false
    }

    if (
      (isCreateMode || form.password || form.confirmPassword) &&
      form.password.trim().length < 8
    ) {
      showError('A senha deve ter no mínimo 8 caracteres.')
      return false
    }

    if (
      (isCreateMode || form.password || form.confirmPassword) &&
      form.password !== form.confirmPassword
    ) {
      showError('Senha e confirmação de senha não coincidem.')
      return false
    }

    return true
  }

  const buildProfilePayload = () => ({
    name: form.name.trim(),
    email: form.email.trim().toLowerCase(),
    cpf: onlyNumbers(form.cpf) || null,
    phone: onlyNumbers(form.phone) || null,
    crm_number: isDoctorRole ? onlyNumbers(form.crm_number) || null : null,
    crm_uf: isDoctorRole ? form.crm_uf || null : null,
  })

  const buildCreatePayload = () => ({
    ...buildProfilePayload(),
    role_id: Number(form.role_id),
    clinic_id: requiresClinic ? Number(form.clinic_id) : null,
  })

  const buildAdminUpdatePayload = () => {
    const payload = buildProfilePayload()

    if (!isSelfRecord && !isClinicManager) {
      payload.role_id = Number(form.role_id)
      payload.clinic_id = requiresClinic ? Number(form.clinic_id) : null
    }

    return payload
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    showError('')
    showSuccess('')

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        await userService.create({
          ...buildCreatePayload(),
          password: form.password.trim(),
        })

        showSuccess(
          isClinicManager ? 'Médico cadastrado com sucesso.' : 'Usuário cadastrado com sucesso.',
        )
        navigate('/users')
        return
      }

      if (isEditMode) {
        await userService.update(id, buildAdminUpdatePayload())

        if (form.password.trim()) {
          await userService.updatePassword(id, form.password.trim())
        }

        showSuccess(
          isClinicManager ? 'Médico atualizado com sucesso.' : 'Usuário atualizado com sucesso.',
        )
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar o usuário.'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">
            {isClinicManager ? 'Equipe Clínica' : 'Controle de Acesso'}
          </div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            {isClinicManager
              ? 'Gerencie os dados cadastrais do médico da sua clínica.'
              : 'Gerencie os dados cadastrais e o perfil de acesso do usuário.'}
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton
            color="secondary"
            size="lg"
            variant="outline"
            className="clinicai-soft-action"
            as={Link}
            to="/users"
          >
            Voltar
          </CButton>
        </div>
      </div>

      {isEditMode && !isSelfRecord && !isClinicManager && (
        <CAlert color="warning">
          Alterar o perfil de acesso ou a clínica encerra as sessões ativas do usuário. O status
          deve ser alterado somente pelos botões Ativar/Inativar da listagem.
        </CAlert>
      )}

      {isEditMode && isSelfRecord && (
        <CAlert color="info">
          Perfil, clínica, status e senha da própria conta não podem ser alterados nesta tela. Use
          “Meu Perfil” para atualizar seus dados ou sua senha.
        </CAlert>
      )}

      <CCard className="mb-4">
        <CCardHeader>
          <strong>{isClinicManager ? 'Dados do Médico' : 'Dados do Usuário'}</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={isClinicManager ? 12 : 8}>
                <CFormLabel>Nome</CFormLabel>
                <CFormInput
                  value={form.name}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('name', event.target.value)}
                  required
                />
              </CCol>

              {!isClinicManager && (
                <CCol md={4}>
                  <CFormLabel>Perfil de acesso</CFormLabel>
                  <CFormSelect
                    value={form.role_id}
                    disabled={isReadOnly || isSelfRecord}
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
              )}

              {!isClinicManager && requiresClinic && (
                <CCol md={isDoctorRole ? 6 : 12}>
                  <CFormLabel>Clínica</CFormLabel>
                  <CFormSelect
                    value={form.clinic_id}
                    disabled={isReadOnly || isSelfRecord}
                    onChange={(event) => updateField('clinic_id', event.target.value)}
                    required
                  >
                    <option value="">Selecione...</option>
                    {availableClinics.map((clinic) => (
                      <option key={clinic.id} value={clinic.id}>
                        {clinic.name}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
              )}

              {isDoctorRole && (
                <>
                  <CCol md={isClinicManager ? 8 : 4}>
                    <CFormLabel>CRM</CFormLabel>
                    <CFormInput
                      value={form.crm_number}
                      disabled={isReadOnly}
                      inputMode="numeric"
                      maxLength={10}
                      onChange={(event) =>
                        updateField('crm_number', onlyNumbers(event.target.value) || '')
                      }
                      placeholder="Número do CRM"
                      required
                    />
                  </CCol>

                  <CCol md={isClinicManager ? 4 : 2}>
                    <CFormLabel>UF do CRM</CFormLabel>
                    <CFormSelect
                      value={form.crm_uf}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('crm_uf', event.target.value)}
                      required
                    >
                      <option value="">Selecione...</option>
                      {brazilianStates.map((state) => (
                        <option key={state} value={state}>
                          {state}
                        </option>
                      ))}
                    </CFormSelect>
                  </CCol>
                </>
              )}

              <CCol md={6}>
                <CFormLabel>CPF</CFormLabel>
                <CFormInput
                  value={form.cpf}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('cpf', formatCpfBR(event.target.value))}
                  placeholder="000.000.000-00"
                  required
                />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Telefone</CFormLabel>
                <CFormInput
                  value={form.phone}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                  placeholder="(88) 99999-9999"
                />
              </CCol>

              <CCol md={!isReadOnly && (!isEditMode || !isSelfRecord) ? 4 : 12}>
                <CFormLabel>E-mail</CFormLabel>
                <CFormInput
                  type="email"
                  value={form.email}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('email', event.target.value)}
                  required
                />
              </CCol>

              {!isReadOnly && (!isEditMode || !isSelfRecord) && (
                <>
                  <CCol md={4}>
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

                  <CCol md={4}>
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
                    {isClinicManager
                      ? 'O perfil Médico e a clínica são definidos automaticamente.'
                      : 'As permissões são definidas automaticamente pelo perfil de acesso selecionado.'}
                  </div>
                </div>
              </CCol>
            </CRow>

            {!isReadOnly && (
              <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
                <CButton color="primary" type="submit" disabled={isSaving}>
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </CButton>

                <CButton color="secondary" variant="outline" as={Link} to="/users">
                  Cancelar
                </CButton>
              </div>
            )}
          </CForm>
        </CCardBody>
      </CCard>

      {!isCreateMode && isDoctorRole && (
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Pacientes ({doctorPatients.length})</strong>
          </CCardHeader>

          <CCardBody
            style={{
              maxHeight: '420px',
              overflowY: 'auto',
            }}
            tabIndex={0}
            aria-label="Pacientes vinculados ao médico"
          >
            {doctorPatients.length === 0 ? (
              <div className="text-body-secondary">Nenhum paciente vinculado a este médico.</div>
            ) : (
              <CRow className="g-3">
                {doctorPatients.map((patient) => (
                  <CCol key={patient.id} xs={12} md={6} lg={4}>
                    <CCard className="h-100 border shadow-sm">
                      <CCardBody className="d-flex flex-column p-3">
                        <div className="d-flex justify-content-between align-items-start gap-2">
                          <div className="fw-semibold">{patient.name}</div>

                          <CBadge color={statusColors[patient.status_name] || 'secondary'}>
                            {patient.status_display_name ||
                              (patient.status_name === 'active' ? 'Ativo' : 'Inativo')}
                          </CBadge>
                        </div>

                        <div className="text-body-secondary small mt-3">
                          CPF: {formatCpfBR(patient.cpf)}
                        </div>

                        <div className="text-body-secondary small mt-1">
                          Telefone: {formatPhoneBR(patient.phone) || 'Não informado'}
                        </div>

                        <div className="text-body-secondary small mt-1">
                          Exames: {patient.exam_count}
                        </div>

                        <CButton
                          color="primary"
                          variant="outline"
                          size="sm"
                          className="clinicai-soft-action mt-2 pt-2"
                          as={Link}
                          to={`/patients/${patient.id}`}
                        >
                          Ver paciente
                        </CButton>
                      </CCardBody>
                    </CCard>
                  </CCol>
                ))}
              </CRow>
            )}
          </CCardBody>
        </CCard>
      )}
    </>
  )
}

export default UserForm
