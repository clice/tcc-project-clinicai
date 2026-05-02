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

import {
  aiAnalyses as aiAnalysesMock,
  clinics as clinicsMock,
  exams as examsMock,
  patients as patientsMock,
  statuses as statusesMock,
  users as usersMock,
} from 'src/mocks/data'

const emptyExam = {
  clinic_id: '',
  patient_id: '',
  doctor_id: '',
  status_id: '',

  exam_type: '',
  exam_date: '',

  title: '',
  description: '',
  clinical_indication: '',
  findings: '',
  conclusion: '',

  ai_analysis_status: 'not_processed',
  ai_summary: '',

  file_path: '',
  file_name: '',
  file_mime_type: '',
}

const examTypeOptions = [
  { value: 'endoscopy', label: 'Endoscopia' },
  { value: 'colonoscopy', label: 'Colonoscopia' },
]

const aiStatusLabels = {
  not_processed: 'Não processado',
  processing: 'Processando',
  completed: 'Concluída',
  failed: 'Falhou',
}

const aiStatusColors = {
  not_processed: 'secondary',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
}

const formatConfidence = (value) => {
  if (value === undefined || value === null) return '-'

  return `${Math.round(value * 100)}%`
}

const ExamForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyExam)
  const [clinics, setClinics] = useState([])
  const [patients, setPatients] = useState([])
  const [doctors, setDoctors] = useState([])
  const [statuses, setStatuses] = useState([])
  const [aiAnalysis, setAiAnalysis] = useState(null)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

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

  const availableDoctors = useMemo(() => {
    if (!form.clinic_id) return []

    return doctors.filter(
      (doctor) =>
        String(doctor.clinic_id) === String(form.clinic_id) &&
        doctor.role_name === 'doctor' &&
        doctor.status_name === 'active',
    )
  }, [doctors, form.clinic_id])

  const examStatuses = useMemo(() => {
    return statuses.filter((status) => status.applies_to === 'exams')
  }, [statuses])

  useEffect(() => {
    setIsLoading(true)
    setError('')
    setSuccess('')

    setClinics(Array.isArray(clinicsMock) ? clinicsMock : [])
    setPatients(Array.isArray(patientsMock) ? patientsMock : [])
    setDoctors(Array.isArray(usersMock) ? usersMock : [])
    setStatuses(Array.isArray(statusesMock) ? statusesMock : [])

    if (isCreateMode) {
      const processingStatus = statusesMock.find(
        (status) => status.applies_to === 'exams' && status.name === 'processing',
      )

      setForm({
        ...emptyExam,
        status_id: processingStatus ? String(processingStatus.id) : '',
      })

      setAiAnalysis(null)
      setIsLoading(false)
      return
    }

    const examData = examsMock.find((exam) => String(exam.id) === String(id))

    if (!examData) {
      setError('Exame não encontrado no mock.')
      setIsLoading(false)
      return
    }

    const analysisData = aiAnalysesMock.find(
      (analysis) => String(analysis.exam_id) === String(examData.id),
    )

    setForm({
      clinic_id: examData.clinic_id ? String(examData.clinic_id) : '',
      patient_id: examData.patient_id ? String(examData.patient_id) : '',
      doctor_id: examData.doctor_id ? String(examData.doctor_id) : '',
      status_id: examData.status_id ? String(examData.status_id) : '',

      exam_type: examData.exam_type ?? '',
      exam_date: examData.exam_date ?? '',

      title: examData.title ?? '',
      description: examData.description ?? '',
      clinical_indication: examData.clinical_indication ?? '',
      findings: examData.findings ?? '',
      conclusion: examData.conclusion ?? '',

      ai_analysis_status: examData.ai_analysis_status ?? 'not_processed',
      ai_summary: examData.ai_summary ?? '',

      file_path: examData.file_path ?? '',
      file_name: examData.file_name ?? '',
      file_mime_type: examData.file_mime_type ?? '',
    })

    setAiAnalysis(analysisData ?? null)
    setIsLoading(false)
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
      doctor_id: patient?.doctor_id ? String(patient.doctor_id) : current.doctor_id,
    }))
  }

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]

    if (!file) {
      updateField('file_name', '')
      updateField('file_mime_type', '')
      updateField('file_path', '')
      return
    }

    setForm((current) => ({
      ...current,
      file_name: file.name,
      file_mime_type: file.type,
      file_path: `uploads/exams/${file.name}`,
    }))
  }

  const validateForm = () => {
    if (!form.clinic_id) {
      setError('Selecione a clínica do exame.')
      return false
    }

    if (!form.patient_id) {
      setError('Selecione o paciente do exame.')
      return false
    }

    if (!form.status_id) {
      setError('Selecione o status do exame.')
      return false
    }

    if (!form.exam_type) {
      setError('Selecione o tipo do exame.')
      return false
    }

    if (!form.title.trim()) {
      setError('Informe o título do exame.')
      return false
    }

    return true
  }

  const buildPayload = () => {
    const clinic = clinics.find((item) => String(item.id) === String(form.clinic_id))
    const patient = patients.find((item) => String(item.id) === String(form.patient_id))
    const doctor = doctors.find((item) => String(item.id) === String(form.doctor_id))
    const status = statuses.find((item) => String(item.id) === String(form.status_id))

    return {
      clinic_id: Number(form.clinic_id),
      clinic_name: clinic?.name ?? null,

      patient_id: Number(form.patient_id),
      patient_name: patient?.name ?? null,

      doctor_id: form.doctor_id ? Number(form.doctor_id) : null,
      doctor_name: doctor?.name ?? null,

      status_id: Number(form.status_id),
      status_name: status?.name ?? null,
      status_display_name: status?.display_name ?? null,

      exam_type: form.exam_type,
      exam_date: form.exam_date || null,

      title: form.title.trim(),
      description: form.description.trim() || null,
      clinical_indication: form.clinical_indication.trim() || null,
      findings: form.findings.trim() || null,
      conclusion: form.conclusion.trim() || null,

      ai_analysis_status: form.ai_analysis_status || 'not_processed',
      ai_summary: form.ai_summary.trim() || null,

      file_path: form.file_path || null,
      file_name: form.file_name || null,
      file_mime_type: form.file_mime_type || null,
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

      const payload = buildPayload()

      console.log('Payload mock de exame:', payload)

      if (isCreateMode) {
        setSuccess('Exame cadastrado com sucesso no mock.')
        navigate('/exams')
        return
      }

      if (isEditMode) {
        setSuccess('Exame atualizado com sucesso no mock.')
      }
    } catch (err) {
      setError(err.message || 'Erro ao salvar exame.')
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
            Cadastro de exame com suporte futuro para análise por IA.
          </p>
        </div>

        <CButton color="secondary" size="lg" variant="outline" as={Link} to="/exams">
          Voltar
        </CButton>
      </div>

      <CRow className="g-4">
        <CCol lg={8}>
          <CCard>
            <CCardHeader>
              <strong>Dados do Exame</strong>
            </CCardHeader>

            <CCardBody>
              {error && <CAlert color="danger">{error}</CAlert>}
              {success && <CAlert color="success">{success}</CAlert>}

              {isLoading ? (
                <p className="text-body-secondary mb-0">Carregando exame...</p>
              ) : (
                <CForm onSubmit={handleSubmit}>
                  <CRow className="g-3">
                    <CCol md={6}>
                      <CFormLabel>Clínica</CFormLabel>
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
                    </CCol>

                    <CCol md={6}>
                      <CFormLabel>Paciente</CFormLabel>
                      <CFormSelect
                        value={form.patient_id}
                        disabled={isReadOnly || !form.clinic_id}
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
                    </CCol>

                    <CCol md={6}>
                      <CFormLabel>Médico responsável</CFormLabel>
                      <CFormSelect
                        value={form.doctor_id}
                        disabled={isReadOnly || !form.clinic_id}
                        onChange={(event) => updateField('doctor_id', event.target.value)}
                      >
                        <option value="">Selecione...</option>

                        {availableDoctors.map((doctor) => (
                          <option key={doctor.id} value={doctor.id}>
                            {doctor.name}
                          </option>
                        ))}
                      </CFormSelect>
                    </CCol>

                    <CCol md={6}>
                      <CFormLabel>Status</CFormLabel>
                      <CFormSelect
                        value={form.status_id}
                        disabled={isReadOnly}
                        onChange={(event) => updateField('status_id', event.target.value)}
                        required
                      >
                        <option value="">Selecione...</option>

                        {examStatuses.map((status) => (
                          <option key={status.id} value={status.id}>
                            {status.display_name}
                          </option>
                        ))}
                      </CFormSelect>
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
                        placeholder="Ex: Colonoscopia - Nome do Paciente"
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
                        onChange={(event) => updateField('description', event.target.value)}
                      />
                    </CCol>

                    <CCol md={12}>
                      <CFormLabel>Indicação clínica</CFormLabel>
                      <CFormTextarea
                        rows={2}
                        value={form.clinical_indication}
                        disabled={isReadOnly}
                        onChange={(event) =>
                          updateField('clinical_indication', event.target.value)
                        }
                      />
                    </CCol>

                    <CCol md={12}>
                      <CFormLabel>Achados</CFormLabel>
                      <CFormTextarea
                        rows={3}
                        value={form.findings}
                        disabled={isReadOnly}
                        onChange={(event) => updateField('findings', event.target.value)}
                      />
                    </CCol>

                    <CCol md={12}>
                      <CFormLabel>Conclusão</CFormLabel>
                      <CFormTextarea
                        rows={3}
                        value={form.conclusion}
                        disabled={isReadOnly}
                        onChange={(event) => updateField('conclusion', event.target.value)}
                      />
                    </CCol>

                    <CCol md={12}>
                      <CFormLabel>Arquivo do exame</CFormLabel>

                      {!isReadOnly && (
                        <CFormInput
                          type="file"
                          accept="image/*,.pdf"
                          onChange={handleFileChange}
                        />
                      )}

                      <div className="text-body-secondary small mt-2">
                        {form.file_name
                          ? `Arquivo selecionado: ${form.file_name}`
                          : 'Nenhum arquivo selecionado.'}
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
              )}
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
                <div>{form.ai_summary || 'Nenhum resumo de IA disponível.'}</div>
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