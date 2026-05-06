/**
 * Formulário do módulo de Exams.
 *
 * Permite cadastrar, visualizar e editar exames.
 * Também exibe uma área preparada para análise de IA.
 */

import React, { useEffect, useMemo, useState } from 'react'
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
  CFormTextarea,
  CRow,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'

import { examTypeOptions, aiStatusLabels, aiStatusColors } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import { getUserRole, ROLES } from 'src/utils/permissions'

const allowedImageTypes = ['image/jpeg', 'image/png']

const emptyExam = {
  clinic_id: '',
  patient_id: '',
  doctor_id: '',
  exam_type: '',
  exam_date: '',
  title: '',
  description: '',
  clinical_indication: '',
  status_id: '',
  status_name: '',
  status_display_name: '',
  ai_analysis_status: 'processing',
  ai_summary: '',
  file_path: '',
  file_name: '',
  file_mime_type: '',
}

const formatConfidence = (value) => {
  if (value === undefined || value === null) return '-'
  return `${Math.round(value * 100)}%`
}

const ExamForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyExam)
  const [clinics, setClinics] = useState([])
  const [patients, setPatients] = useState([])
  const [doctors, setDoctors] = useState([])
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const roleName = getUserRole(user)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isDoctor = roleName === ROLES.DOCTOR

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Exame'
    if (isEditMode) return 'Editar Exame'
    return 'Detalhes do Exame'
  }, [isCreateMode, isEditMode])

  const activeClinics = useMemo(() => {
    const selectedClinicId = String(form.clinic_id)

    return clinics.filter((clinic) => {
      const isActive = clinic.status_name === 'active'
      const isSelected = String(clinic.id) === selectedClinicId

      return isActive || isSelected
    })
  }, [clinics, form.clinic_id])

  const availablePatients = useMemo(() => {
    if (!form.clinic_id) return []

    return patients.filter(
      (patient) =>
        String(patient.clinic_id) === String(form.clinic_id) &&
        patient.status_name === 'active',
    )
  }, [patients, form.clinic_id])

  const selectedClinicName = useMemo(() => {
    const clinic = clinics.find((item) => String(item.id) === String(form.clinic_id))
    return clinic?.name || '-'
  }, [clinics, form.clinic_id])

  const selectedPatientName = useMemo(() => {
    const patient = patients.find((item) => String(item.id) === String(form.patient_id))
    return patient?.name || '-'
  }, [patients, form.patient_id])

  const selectedDoctorName = useMemo(() => {
    const doctor = doctors.find((item) => String(item.id) === String(form.doctor_id))
    return doctor?.name || '-'
  }, [doctors, form.doctor_id])

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        showError('')
        showSuccess('')

        const options = await examService.getFormOptions()

        const loadedClinics = options.clinics || []
        const loadedPatients = options.patients || []
        const loadedDoctors = options.doctors || []

        setClinics(loadedClinics)
        setPatients(loadedPatients)
        setDoctors(loadedDoctors)

        if (isCreateMode) {
          setForm({
            ...emptyExam,
            clinic_id: loadedClinics.length === 1 ? String(loadedClinics[0].id) : '',
          })

          setAiAnalysis(null)
          return
        }

        const examData = await examService.getById(id)

        setForm({
          clinic_id: examData.clinic_id ? String(examData.clinic_id) : '',
          patient_id: examData.patient_id ? String(examData.patient_id) : '',
          doctor_id: examData.doctor_id ? String(examData.doctor_id) : '',

          exam_type: examData.exam_type ?? '',
          exam_date: examData.exam_date ?? '',

          title: examData.title ?? '',
          description: examData.description ?? '',
          clinical_indication: examData.clinical_indication ?? '',

          status_id: examData.status_id ? String(examData.status_id) : '',
          status_name: examData.status_name ?? '',
          status_display_name: examData.status_display_name ?? '',

          ai_analysis_status: examData.status_name || 'processing',
          ai_summary: examData.ai_summary ?? '',

          file_path: examData.file_path ?? '',
          file_name: examData.file_name ?? '',
          file_mime_type: examData.file_mime_type ?? '',
        })

        setAiAnalysis(null)
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados do exame.'))
      } finally {
        setIsLoading(false)
      }
    }

    void loadData()
  }, [id, isCreateMode])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleClinicChange = (clinicId) => {
    setForm((current) => ({
      ...current,
      clinic_id: clinicId,
      patient_id: '',
      doctor_id: '',
    }))
  }

  const handlePatientChange = (patientId) => {
    const patient = patients.find((item) => String(item.id) === String(patientId))

    setForm((current) => ({
      ...current,
      patient_id: patientId,
      doctor_id: patient?.doctor_id ? String(patient.doctor_id) : '',
    }))
  }

  const handleFileChange = (event) => {
    const file = event.target.files?.[0] || null

    setSelectedFile(file)

    setForm((current) => ({
      ...current,
      file_name: file?.name || '',
      file_mime_type: file?.type || '',
    }))
  }

  const validateForm = () => {
    if (!form.clinic_id) {
      showError('Selecione a clínica do exame.')
      return false
    }

    if (!form.patient_id) {
      showError('Selecione o paciente do exame.')
      return false
    }

    if (!form.doctor_id) {
      showError('O paciente selecionado precisa ter um médico responsável vinculado.')
      return false
    }

    if (!form.exam_type) {
      showError('Selecione o tipo do exame.')
      return false
    }

    if (!form.title.trim()) {
      showError('Informe o título do exame.')
      return false
    }

    if (isCreateMode && !selectedFile) {
      showError('A imagem do exame é obrigatória.')
      return false
    }

    if (selectedFile && !allowedImageTypes.includes(selectedFile.type)) {
      showError('Formato inválido. Envie uma imagem JPG, JPEG ou PNG.')
      return false
    }

    return true
  }

  const buildCreatePayload = () => ({
    clinic_id: Number(form.clinic_id),
    patient_id: Number(form.patient_id),
    doctor_id: Number(form.doctor_id),

    exam_type: form.exam_type,
    exam_date: form.exam_date || null,

    title: form.title.trim(),
    description: form.description.trim() || null,
    clinical_indication: form.clinical_indication.trim() || null,

    file: selectedFile,
  })

  const buildUpdatePayload = () => ({
    exam_type: form.exam_type,
    exam_date: form.exam_date || null,

    title: form.title.trim(),
    description: form.description.trim() || null,
    clinical_indication: form.clinical_indication.trim() || null,
  })

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    showError('')
    showSuccess('')

    console.log('SUBMIT START')
    console.log('MODE:', mode)
    console.log('IS READ ONLY:', isReadOnly)
    console.log('IS EDIT MODE:', isEditMode)
    console.log('FORM:', form)

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        const payload = buildCreatePayload()
        console.log('CREATE PAYLOAD:', payload)

        await examService.create(payload)
      }

      if (isEditMode) {
        const payload = buildUpdatePayload()
        console.log('UPDATE PAYLOAD:', payload)

        await examService.update(id, payload)
      }

      showSuccess('Exame salvo com sucesso.')
      navigate('/exams')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar exame.'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            Cadastro inicial do exame com imagem obrigatória para análise por IA.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/exams">
            Voltar
          </CButton>
        </div>
      </div>

      <CRow className="g-4">
        <CCol lg={8}>
          <CCard>
            <CCardHeader>
              <strong>Dados iniciais do exame</strong>
            </CCardHeader>

            <CCardBody>
              <CForm onSubmit={handleSubmit}>
                <CRow className="g-3">
                  <CCol md={6}>
                    <CFormLabel>Clínica</CFormLabel>

                    {isCreateMode ? (
                      <CFormSelect
                        value={form.clinic_id}
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
                      <CFormInput value={selectedClinicName} disabled />
                    )}

                    {!isCreateMode && (
                      <div className="text-body-secondary small mt-1">
                        A clínica não pode ser alterada após o cadastro do exame.
                      </div>
                    )}
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Paciente</CFormLabel>

                    {isCreateMode ? (
                      <CFormSelect
                        value={form.patient_id}
                        disabled={!form.clinic_id}
                        onChange={(event) => handlePatientChange(event.target.value)}
                        required
                      >
                        <option value="">
                          {form.clinic_id
                            ? 'Selecione...'
                            : 'Selecione uma clínica primeiro'}
                        </option>

                        {availablePatients.map((patient) => (
                          <option key={patient.id} value={patient.id}>
                            {patient.name}
                          </option>
                        ))}
                      </CFormSelect>
                    ) : (
                      <CFormInput value={selectedPatientName} disabled />
                    )}

                    {!isCreateMode && (
                      <div className="text-body-secondary small mt-1">
                        O paciente não pode ser alterado após o cadastro do exame.
                      </div>
                    )}
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Médico responsável</CFormLabel>
                    <CFormInput value={selectedDoctorName} disabled />

                    <div className="text-body-secondary small mt-1">
                      O médico é definido automaticamente pelo paciente selecionado.
                    </div>
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Status</CFormLabel>
                    <CFormInput
                      value={
                        form.status_display_name ||
                        (isCreateMode ? 'Processando após o cadastro' : '-')
                      }
                      disabled
                    />

                    <div className="text-body-secondary small mt-1">
                      O status é controlado automaticamente pelo fluxo do sistema.
                    </div>
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Tipo de exame</CFormLabel>
                    <CFormSelect
                      value={form.exam_type}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('exam_type', event.target.value)}
                      required
                    >
                      <option value="">Selecione...</option>

                      {examTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </CFormSelect>
                  </CCol>

                  <CCol md={6}>
                    <CFormLabel>Data do exame</CFormLabel>
                    <CFormInput
                      type="date"
                      value={form.exam_date}
                      disabled={isReadOnly}
                      onChange={(event) => updateField('exam_date', event.target.value)}
                    />
                  </CCol>

                  <CCol md={12}>
                    <CFormLabel>Título</CFormLabel>
                    <CFormInput
                      value={form.title}
                      disabled={isReadOnly}
                      placeholder="Ex: Colonoscopia - rastreamento"
                      onChange={(event) => updateField('title', event.target.value)}
                      required
                    />
                  </CCol>

                  <CCol md={12}>
                    <CFormLabel>Descrição</CFormLabel>
                    <CFormTextarea
                      rows={2}
                      value={form.description}
                      disabled={isReadOnly}
                      placeholder="Descrição breve do exame, se necessário."
                      onChange={(event) => updateField('description', event.target.value)}
                    />
                  </CCol>

                  <CCol md={12}>
                    <CFormLabel>Indicação clínica</CFormLabel>
                    <CFormTextarea
                      rows={2}
                      value={form.clinical_indication}
                      disabled={isReadOnly}
                      placeholder="Ex: dor abdominal, rastreamento, refluxo persistente..."
                      onChange={(event) =>
                        updateField('clinical_indication', event.target.value)
                      }
                    />
                  </CCol>

                  <CCol md={12}>
                    <CFormLabel>Imagem do exame</CFormLabel>

                    {isCreateMode ? (
                      <CFormInput
                        type="file"
                        accept="image/jpeg,image/png"
                        onChange={handleFileChange}
                        required
                      />
                    ) : (
                      <CFormInput value={form.file_name || 'Nenhum arquivo vinculado'} disabled />
                    )}

                    <div className="text-body-secondary small mt-2">
                      {isCreateMode
                        ? 'Envie uma imagem em formato JPG, JPEG ou PNG.'
                        : 'A imagem original não pode ser alterada nesta tela.'}
                    </div>
                  </CCol>
                </CRow>

                {!isReadOnly && (
                  <CButtonGroup className="mt-4">
                    <CButton color="primary" type="submit" disabled={isSaving}>
                      {isSaving ? 'Salvando...' : 'Salvar'}
                    </CButton>

                    <CButton color="secondary" variant="outline" as={Link} to="/exams">
                      Cancelar
                    </CButton>
                  </CButtonGroup>
                )}
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>

        <CCol lg={4}>
          <CCard className="mb-4">
            <CCardHeader>
              <strong>Análise por IA</strong>
            </CCardHeader>

            <CCardBody>
              <div className="mb-3">
                <div className="text-body-secondary small">Status da análise</div>
                <CBadge color={aiStatusColors[form.ai_analysis_status] || 'secondary'}>
                  {aiStatusLabels[form.ai_analysis_status] || form.ai_analysis_status}
                </CBadge>
              </div>

              <div className="mb-3">
                <div className="text-body-secondary small">Resumo</div>
                <div>{form.ai_summary || 'A análise será executada após o cadastro.'}</div>
              </div>

              {aiAnalysis ? (
                <>
                  <hr />

                  <div className="mb-3">
                    <div className="text-body-secondary small">Predição</div>
                    <strong>{aiAnalysis.prediction_label}</strong>
                  </div>

                  <div className="mb-3">
                    <div className="text-body-secondary small">Confiança</div>
                    <strong>{formatConfidence(aiAnalysis.confidence)}</strong>
                  </div>

                  <div className="mb-3">
                    <div className="text-body-secondary small">Modelo</div>
                    <div>
                      {aiAnalysis.model_name} v{aiAnalysis.model_version}
                    </div>
                  </div>

                  <div className="mb-3">
                    <div className="text-body-secondary small">Tempo de processamento</div>
                    <div>
                      {aiAnalysis.processing_time_ms
                        ? `${aiAnalysis.processing_time_ms} ms`
                        : '-'}
                    </div>
                  </div>

                  <div className="mb-3">
                    <div className="text-body-secondary small">Grad-CAM</div>
                    <div>{aiAnalysis.gradcam_path || 'Não disponível.'}</div>
                  </div>

                  <div>
                    <div className="text-body-secondary small">Observações da IA</div>
                    <div>{aiAnalysis.ai_notes || '-'}</div>
                  </div>
                </>
              ) : (
                <CAlert color="secondary" className="mb-0">
                  Este exame ainda não possui análise de IA vinculada.
                </CAlert>
              )}
            </CCardBody>
          </CCard>

          <CCard>
            <CCardHeader>
              <strong>Arquivo</strong>
            </CCardHeader>

            <CCardBody>
              <div className="mb-2">
                <div className="text-body-secondary small">Nome</div>
                <div>{form.file_name || '-'}</div>
              </div>

              <div className="mb-2">
                <div className="text-body-secondary small">Tipo</div>
                <div>{form.file_mime_type || '-'}</div>
              </div>

              <div>
                <div className="text-body-secondary small">Caminho</div>
                <div className="text-break">{form.file_path || '-'}</div>
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </>
  )
}

export default ExamForm