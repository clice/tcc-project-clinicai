/**
 * Formulário do módulo de Petients.
 *
 * Usado para:
 * - criar paciente;
 * - visualizar paciente;
 * - editar paciente.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
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
  CListGroup,
  CListGroupItem,
  CRow,
  CSpinner,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { addressService } from 'src/services/addressService'
import { patientService } from 'src/services/patientService'
import { clinicService } from 'src/services/clinicService'
import { userService } from 'src/services/userService'

import { getErrorMessage } from 'src/utils/errors'
import { formatCpfBR, formatPhoneBR, formatZipCodeBR, onlyNumbers } from 'src/utils/formatters'
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

  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'
  const isViewMode = mode === 'view'
  const isArchiveMode = mode === 'archive'
  const isReadOnly = isViewMode || isArchiveMode

  const roleName = getUserRole(user)
  const canCreateExam = hasPermission(user, PERMISSIONS.EXAMS_CREATE)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isDoctor = roleName === ROLES.DOCTOR

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

  const loadDoctorsByClinic = useCallback(async (clinicId) => {
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
  }, [])

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
  ])

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

  const buildPayload = () => ({
    clinic_id: Number(form.clinic_id || user?.clinic_id),
    doctor_id: isDoctor ? Number(user.id) : Number(form.doctor_id),
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
  })

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
        await patientService.update(id, buildPayload())
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
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">Cadastro clínico e administrativo do paciente.</p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButtonGroup>
            {patient && canCreateExam && (
              <CButton
                color="info"
                size="lg"
                as={Link}
                to={`/exams/upload?patient=${id}`}
                className="text-white"
              >
                Upload exame
              </CButton>
            )}

            <CButton color="secondary" size="lg" variant="outline" as={Link} to="/patients">
              Voltar
            </CButton>
          </CButtonGroup>
        </div>
      </div>

      <CRow className="g-4">
        <CCol lg={8}>
          <CCard>
            <CCardHeader>
              <strong>Dados do paciente</strong>
            </CCardHeader>

            <CCardBody>
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

                  <CCol md={4}>
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
                    <CFormLabel>Médico responsável</CFormLabel>

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

                  <CCol md={4}>
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

                  <CCol md={4}>
                    <CFormLabel>Número</CFormLabel>
                    <CFormInput
                      value={form.number}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('number', event.target.value)}
                    />
                  </CCol>

                  <CCol md={8}>
                    <CFormLabel>Complemento</CFormLabel>
                    <CFormInput value={form.complement} disabled />
                  </CCol>

                  <CCol md={4}>
                    <CFormLabel>Bairro</CFormLabel>
                    <CFormInput value={form.neighborhood} disabled />
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Cidade</CFormLabel>
                    <CFormInput value={form.city} disabled />
                  </CCol>

                  <CCol md={2}>
                    <CFormLabel>UF</CFormLabel>
                    <CFormInput value={form.state} disabled maxLength={2} />
                  </CCol>
                </CRow>

                {!isReadOnly && (
                  <CButtonGroup className="mt-4">
                    <CButton color="primary" type="submit" disabled={isSaving}>
                      {isSaving ? 'Salvando...' : 'Salvar'}
                    </CButton>

                    <CButton color="secondary" variant="outline" as={Link} to="/patients">
                      Cancelar
                    </CButton>
                  </CButtonGroup>
                )}
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>

        <CCol lg={4}>
          <CCard>
            <CCardHeader>
              <strong>Histórico de Exames</strong>
            </CCardHeader>

            <CCardBody>
              <CListGroup flush>
                <CListGroupItem>
                  Nenhum exame registrado ainda.
                  <small className="d-block text-body-secondary mt-1">
                    Área preparada para o módulo Exams.
                  </small>
                </CListGroupItem>
              </CListGroup>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </>
  )
}

export default PatientForm
