/**
 * Formulário do módulo de Patients.
 *
 * Usado para:
 * - criar paciente;
 * - editar paciente.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  CAlert,
  CBadge,
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

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { addressService } from 'src/services/addressService'
import { examService } from 'src/services/examService'
import { patientService } from 'src/services/patientService'
import { clinicService } from 'src/services/clinicService'
import { userService } from 'src/services/userService'

import { examStatusDisplayLabels, examTypeLabels, statusColors } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import {
  formatCpfBR,
  formatDateBR,
  formatPhoneBR,
  formatZipCodeBR,
  onlyNumbers,
} from 'src/utils/formatters'
import { getUserRole, hasPermission, PERMISSIONS, ROLES } from 'src/utils/permissions'

const emptyPatient = {
  clinic_id: '',
  clinic_name: '',
  doctor_id: '',
  doctor_name: '',
  name: '',
  cpf: '',
  birth_date: '',
  sex: '',
  phone: '',
  email: '',
  zip_code: '',
  address: '',
  number: '',
  complement: '',
  neighborhood: '',
  city: '',
  state: '',
  status_name: '',
  status_display_name: '',
}

const PatientForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyPatient)
  const [patient, setPatient] = useState(null)
  const [clinics, setClinics] = useState([])
  const [doctors, setDoctors] = useState([])
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingDoctors, setIsLoadingDoctors] = useState(false)
  const [isLoadingAddress, setIsLoadingAddress] = useState(false)
  const [patientExams, setPatientExams] = useState([])

  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'
  const isArchiveMode = mode === 'archive'
  const isReadOnly = isArchiveMode

  const roleName = getUserRole(user)
  const canCreateExam = hasPermission(user, PERMISSIONS.EXAMS_CREATE)
  const canListExams = hasPermission(user, PERMISSIONS.EXAMS_LIST)
  const canReadExams = hasPermission(user, PERMISSIONS.EXAMS_READ)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isDoctor = roleName === ROLES.DOCTOR
  const hasPatientExams = patientExams.length > 0

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Paciente'
    if (isEditMode) return 'Editar Paciente'
    return 'Detalhes do Paciente'
  }, [isCreateMode, isEditMode])

  const activeClinics = useMemo(() => {
    const selectedClinicId = String(form.clinic_id)

    return clinics.filter((clinic) => {
      const isActive = clinic.status_name === 'active'
      const isSelected = String(clinic.id) === selectedClinicId

      return isActive || isSelected
    })
  }, [clinics, form.clinic_id])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const loadDoctorsByClinic = useCallback(
    async (clinicId) => {
      if (!clinicId) {
        setDoctors([])
        return
      }

      try {
        setIsLoadingDoctors(true)

        const data = await userService.listDoctorsByClinic(clinicId)
        setDoctors(Array.isArray(data) ? data : [])
      } catch (err) {
        setDoctors([])
        showError(getErrorMessage(err, 'Erro ao carregar dados do paciente.'))
      } finally {
        setIsLoadingDoctors(false)
      }
    },
    [showError],
  )

  useEffect(() => {
    const loadData = async () => {
      try {
        startLoading()
        showError('')
        showSuccess('')

        const [clinicsData, patientData] = await Promise.all([
          isAdminMaster ? clinicService.list({ includeInactive: true }) : Promise.resolve([]),
          isCreateMode ? Promise.resolve(null) : patientService.getById(id),
        ])

        const loadedClinics = Array.isArray(clinicsData) ? clinicsData : []
        setClinics(loadedClinics)

        if (patientData) {
          setPatient(patientData)

          setForm({
            clinic_id: patientData.clinic_id ? String(patientData.clinic_id) : '',
            clinic_name: patientData.clinic_name ?? '',
            doctor_id: patientData.doctor_id ? String(patientData.doctor_id) : '',
            doctor_name: patientData.doctor_name ?? '',
            name: patientData.name ?? '',
            cpf: formatCpfBR(patientData.cpf ?? ''),
            birth_date: patientData.birth_date ?? '',
            sex: patientData.sex ?? '',
            phone: formatPhoneBR(patientData.phone ?? ''),
            email: patientData.email ?? '',
            zip_code: formatZipCodeBR(patientData.zip_code ?? ''),
            address: patientData.address ?? '',
            number: patientData.number ?? '',
            complement: patientData.complement ?? '',
            neighborhood: patientData.neighborhood ?? '',
            city: patientData.city ?? '',
            state: patientData.state ?? '',
            status_name: patientData.status_name ?? '',
            status_display_name: patientData.status_display_name ?? '',
          })

          await loadDoctorsByClinic(patientData.clinic_id)
          return
        }

        const clinicId = isAdminMaster ? '' : user?.clinic_id ? String(user.clinic_id) : ''

        setForm({
          ...emptyPatient,
          clinic_id: clinicId,
          clinic_name: user?.clinic_name ?? '',
          doctor_id: isDoctor && user?.id ? String(user.id) : '',
          doctor_name: isDoctor ? (user?.name ?? '') : '',
        })

        if (clinicId) {
          await loadDoctorsByClinic(clinicId)
        }
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar os dados do paciente.'))
      } finally {
        stopLoading()
      }
    }

    void loadData()
  }, [
    id,
    isCreateMode,
    isAdminMaster,
    isDoctor,
    user?.clinic_id,
    user?.clinic_name,
    user?.id,
    user?.name,
    loadDoctorsByClinic,
    showError,
    showSuccess,
    startLoading,
    stopLoading,
  ])

  useEffect(() => {
    if (isCreateMode || !id || !canListExams) {
      return undefined
    }

    let isCancelled = false

    const loadPatientExams = async () => {
      try {
        const data = await examService.list({
          patientId: id,
          includeInactive: true,
        })

        if (isCancelled) return

        const exams = Array.isArray(data) ? [...data] : []

        exams.sort((firstExam, secondExam) => {
          const firstDate = firstExam.exam_date || firstExam.created_at || ''

          const secondDate = secondExam.exam_date || secondExam.created_at || ''

          const dateComparison = secondDate.localeCompare(firstDate)

          if (dateComparison !== 0) {
            return dateComparison
          }

          return Number(secondExam.id) - Number(firstExam.id)
        })

        setPatientExams(exams)
      } catch (err) {
        if (!isCancelled) {
          setPatientExams([])
          showError(getErrorMessage(err, 'Não foi possível carregar os exames do paciente.'))
        }
      }
    }

    void loadPatientExams()

    return () => {
      isCancelled = true
    }
  }, [canListExams, id, isCreateMode, showError])

  const validateForm = () => {
    const cpf = onlyNumbers(form.cpf)
    const phone = onlyNumbers(form.phone)
    const zipCode = onlyNumbers(form.zip_code)

    if (!form.clinic_id && !user?.clinic_id) {
      showError('Selecione a clínica do paciente.')
      return false
    }

    if (!isDoctor && !form.doctor_id) {
      showError('Selecione um médico responsável pelo paciente.')
      return false
    }

    if (!form.name.trim()) {
      showError('Informe o nome do paciente.')
      return false
    }

    if (cpf.length !== 11) {
      showError('CPF deve conter 11 números.')
      return false
    }

    if (phone && phone.length < 10) {
      showError('Telefone deve conter pelo menos 10 dígitos.')
      return false
    }

    if (zipCode && zipCode.length !== 8) {
      showError('CEP deve conter 8 dígitos.')
      return false
    }

    if (form.state && form.state.trim().length !== 2) {
      showError('UF deve conter 2 caracteres.')
      return false
    }

    return true
  }

  const buildPayload = () => {
    const payload = {
      name: form.name.trim(),
      cpf: onlyNumbers(form.cpf),
      birth_date: form.birth_date || null,
      sex: form.sex || null,
      phone: onlyNumbers(form.phone) || null,
      email: form.email.trim() || null,
      zip_code: onlyNumbers(form.zip_code) || null,
      address: form.address.trim() || null,
      number: form.number.trim() || null,
      complement: form.complement.trim() || null,
      neighborhood: form.neighborhood.trim() || null,
      city: form.city.trim() || null,
      state: form.state.trim().toUpperCase() || null,
    }

    // O backend é a fonte da regra: médicos não podem transferir ou
    // reatribuir pacientes. Na criação, os vínculos continuam obrigatórios.
    if (isCreateMode || !isDoctor) {
      payload.clinic_id = Number(form.clinic_id || user?.clinic_id)
      payload.doctor_id = isDoctor ? Number(user.id) : Number(form.doctor_id)
    }

    if (isCreateMode || !patient) return payload

    const originalPayload = {
      name: String(patient.name ?? '').trim(),
      cpf: onlyNumbers(patient.cpf ?? ''),
      birth_date: patient.birth_date || null,
      sex: patient.sex || null,
      phone: onlyNumbers(patient.phone ?? '') || null,
      email: String(patient.email ?? '').trim() || null,
      zip_code: onlyNumbers(patient.zip_code ?? '') || null,
      address: String(patient.address ?? '').trim() || null,
      number: String(patient.number ?? '').trim() || null,
      complement: String(patient.complement ?? '').trim() || null,
      neighborhood: String(patient.neighborhood ?? '').trim() || null,
      city: String(patient.city ?? '').trim() || null,
      state:
        String(patient.state ?? '')
          .trim()
          .toUpperCase() || null,
    }

    if (!isDoctor) {
      originalPayload.clinic_id = Number(patient.clinic_id)
      originalPayload.doctor_id = Number(patient.doctor_id)
    }

    return Object.fromEntries(
      Object.entries(payload).filter(([field, value]) => value !== originalPayload[field]),
    )
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
        await patientService.create(buildPayload())
        navigate('/patients')
        return
      }

      if (isEditMode) {
        const payload = buildPayload()

        if (Object.keys(payload).length === 0) {
          showSuccess('Nenhuma alteração para salvar.')
          return
        }

        const updatedPatient = await patientService.update(id, payload)

        setPatient(updatedPatient)
        setForm((current) => ({
          ...current,
          cpf: formatCpfBR(updatedPatient.cpf ?? ''),
          phone: formatPhoneBR(updatedPatient.phone ?? ''),
          email: updatedPatient.email ?? '',
          zip_code: formatZipCodeBR(updatedPatient.zip_code ?? ''),
          state: updatedPatient.state ?? '',
        }))

        showSuccess('Paciente atualizado com sucesso.')
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar paciente.'))
    } finally {
      setIsSaving(false)
    }
  }

  const handleInactivate = async () => {
    try {
      setIsSaving(true)
      showError('')
      showSuccess('')

      await patientService.inactivate(id)
      navigate('/patients')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao inativar paciente.'))
    } finally {
      setIsSaving(false)
    }
  }

  const handleClinicChange = async (clinicId) => {
    updateField('clinic_id', clinicId)
    updateField('doctor_id', '')

    await loadDoctorsByClinic(clinicId)
  }

  const clearAddressFields = () => {
    setForm((current) => ({
      ...current,
      address: '',
      complement: '',
      neighborhood: '',
      city: '',
      state: '',
    }))
  }

  const handleZipCodeBlur = async () => {
    const zipCode = onlyNumbers(form.zip_code)

    if (!zipCode || zipCode.length !== 8) {
      return
    }

    try {
      setIsLoadingAddress(true)
      showError('')

      clearAddressFields()

      const address = await addressService.getAddressByZipCode(zipCode)

      if (!address) {
        showError('CEP não encontrado.')
        return
      }

      setForm((current) => ({
        ...current,
        zip_code: formatZipCodeBR(address.zip_code),
        address: address.address,
        complement: address.complement,
        neighborhood: address.neighborhood,
        city: address.city,
        state: address.state,
      }))
    } catch {
      showError('Erro ao buscar endereço pelo CEP.')
    } finally {
      setIsLoadingAddress(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0 clinicai-page-title">{title}</h1>
          <p className="text-body-secondary mb-0">Cadastro clínico e administrativo do paciente.</p>
        </div>

        <div className="d-flex justify-content-center mt-4 gap-2">
          {patient?.status_name === 'active' && isDoctor && canCreateExam && (
            <CButton
              color="primary"
              size="lg"
              as={Link}
              to={`/exams/create?patient=${id}`}
              className="clinicai-btn text-white"
            >
              Cadastrar Exame
            </CButton>
          )}

          <CButton
            color="secondary"
            size="lg"
            variant="outline"
            className="clinicai-soft-action"
            as={Link}
            to="/patients"
          >
            Voltar
          </CButton>
        </div>
      </div>

      {isEditMode && (
        <CAlert color="info">
          Esta tela permite alterar os dados do paciente. Revise as informações antes de selecionar
          &quot;Salvar&quot;.
        </CAlert>
      )}

      <CRow className="mb-4 g-4">
        <CCol xs={12}>
          <CCard className="clinicai-card">
            <CCardHeader className="clinicai-card-header">
              <strong>Dados do Paciente</strong>
            </CCardHeader>

            <CCardBody>
              <CForm onSubmit={handleSubmit}>
                <CRow className="g-3">
                  <CCol md={9}>
                    <CFormLabel>Nome</CFormLabel>
                    <CFormInput
                      value={form.name}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('name', event.target.value)}
                      required
                    />
                  </CCol>

                  <CCol md={3}>
                    <CFormLabel>CPF</CFormLabel>
                    <CFormInput
                      value={form.cpf}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('cpf', formatCpfBR(event.target.value))}
                      placeholder="000.000.000-00"
                      required
                    />
                  </CCol>

                  <CCol md={3}>
                    <CFormLabel>Data de Nascimento</CFormLabel>
                    <CFormInput
                      type="date"
                      value={form.birth_date}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('birth_date', event.target.value)}
                    />
                  </CCol>

                  <CCol md={3}>
                    <CFormLabel>Sexo</CFormLabel>
                    <CFormSelect
                      value={form.sex}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('sex', event.target.value)}
                    >
                      <option value="">Selecione</option>
                      <option value="female">Feminino</option>
                      <option value="male">Masculino</option>
                      <option value="other">Outro</option>
                      <option value="not_informed">Não informado</option>
                    </CFormSelect>
                  </CCol>

                  <CCol md={3}>
                    <CFormLabel>Telefone</CFormLabel>
                    <CFormInput
                      value={form.phone}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                      placeholder="(88) 99999-9999"
                    />
                  </CCol>

                  <CCol md={3}>
                    <CFormLabel>E-mail</CFormLabel>
                    <CFormInput
                      type="email"
                      value={form.email}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('email', event.target.value)}
                    />
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Clínica</CFormLabel>

                    {isAdminMaster ? (
                      <CFormSelect
                        value={form.clinic_id}
                        disabled={isReadOnly}
                        onChange={(event) => handleClinicChange(event.target.value)}
                        required
                      >
                        <option value="">Selecione...</option>

                        {activeClinics.map((clinic) => (
                          <option key={clinic.id} value={clinic.id}>
                            {clinic.name}
                          </option>
                        ))}
                      </CFormSelect>
                    ) : (
                      <CFormInput
                        value={form.clinic_name || user?.clinic_name || 'Clínica vinculada'}
                        disabled
                      />
                    )}
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Médico Responsável</CFormLabel>

                    {isDoctor ? (
                      <CFormInput
                        value={form.doctor_name || user?.name || 'Usuário médico'}
                        disabled
                      />
                    ) : (
                      <CFormSelect
                        value={form.doctor_id}
                        disabled={isReadOnly || !form.clinic_id || isLoadingDoctors}
                        onChange={(event) => updateField('doctor_id', event.target.value)}
                        required
                      >
                        <option value="">
                          {isLoadingDoctors
                            ? 'Carregando médicos...'
                            : form.clinic_id
                              ? 'Selecione o médico...'
                              : 'Selecione uma clínica primeiro'}
                        </option>

                        {doctors.map((doctor) => (
                          <option key={doctor.id} value={doctor.id}>
                            {doctor.name}
                          </option>
                        ))}
                      </CFormSelect>
                    )}
                  </CCol>

                  <CCol md={2}>
                    <CFormLabel>CEP</CFormLabel>
                    <CFormInput
                      value={form.zip_code}
                      disabled={isReadOnly || isLoadingAddress}
                      onChange={(event) =>
                        updateField('zip_code', formatZipCodeBR(event.target.value))
                      }
                      onBlur={handleZipCodeBlur}
                      placeholder="00000-000"
                    />
                  </CCol>

                  <CCol md={8}>
                    <CFormLabel>Endereço</CFormLabel>
                    <CFormInput value={form.address} disabled />
                  </CCol>

                  <CCol md={2}>
                    <CFormLabel>Número</CFormLabel>
                    <CFormInput
                      value={form.number}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('number', event.target.value)}
                    />
                  </CCol>

                  <CCol md={10}>
                    <CFormLabel>Complemento</CFormLabel>
                    <CFormInput value={form.complement} disabled />
                  </CCol>

                  <CCol md={2}>
                    <CFormLabel>UF</CFormLabel>
                    <CFormInput value={form.state} disabled maxLength={2} />
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Bairro</CFormLabel>
                    <CFormInput value={form.neighborhood} disabled />
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Cidade</CFormLabel>
                    <CFormInput value={form.city} disabled />
                  </CCol>
                </CRow>

                {!isReadOnly && (
                  <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
                    <CButton color="primary" type="submit" disabled={isSaving}>
                      {isSaving ? 'Salvando...' : 'Salvar'}
                    </CButton>

                    <CButton className="clinicai-modal-cancel-action" variant="outline" as={Link} to="/patients">
                      Cancelar
                    </CButton>
                  </div>
                )}
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>

        {!isCreateMode && hasPatientExams && (
          <CCol xs={12}>
            <CCard className="clinicai-card">
              <CCardHeader className="clinicai-card-header">
                <strong>Histórico de Exames ({patientExams.length})</strong>
              </CCardHeader>

              <CCardBody
                style={{
                  maxHeight: '420px',
                  overflowY: 'auto',
                }}
                tabIndex={0}
                aria-label="Histórico de exames do paciente"
              >
                <CRow className="g-3">
                  {patientExams.map((exam) => (
                    <CCol key={exam.id} xs={12} md={6} lg={4}>
                      <CCard className="h-100 border shadow-sm">
                        <CCardBody className="d-flex flex-column p-3">
                          <div className="d-flex justify-content-between align-items-start gap-2">
                            <div className="fw-semibold">
                              {exam.description || `Exame #${exam.id}`}
                            </div>

                            <CBadge color={statusColors[exam.status_name] || 'secondary'}>
                              {examStatusDisplayLabels[exam.status_name] ||
                                exam.status_display_name ||
                                'Status não informado'}
                            </CBadge>
                          </div>

                          <div className="text-body-secondary small mt-3">
                            {examTypeLabels[exam.exam_type] ||
                              exam.exam_type ||
                              'Tipo não informado'}
                          </div>

                          <div className="text-body-secondary small mt-1">
                            Data do exame: {formatDateBR(exam.exam_date)}
                          </div>

                          {isDoctor && canReadExams && (
                            <CButton
                              color="primary"
                              variant="outline"
                              size="sm"
                              className="clinicai-soft-action mt-2 pt-2"
                              as={Link}
                              to={`/exams/${exam.id}`}
                            >
                              Abrir exame
                            </CButton>
                          )}
                        </CCardBody>
                      </CCard>
                    </CCol>
                  ))}
                </CRow>
              </CCardBody>
            </CCard>
          </CCol>
        )}
      </CRow>
    </>
  )
}

export default PatientForm
