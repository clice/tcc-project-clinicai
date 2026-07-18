/**
 * Formulário do módulo de Exams.
 *
 * Permite cadastrar, visualizar e editar exames.
 * Também exibe uma área preparada para análise de IA.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormTextarea,
  CRow,
  CSpinner,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'
import { aiAnalysisService } from 'src/services/aiAnalysisService'
import ExamAiResultCard from 'src/views/exams/ExamAiResultCard'
import ExamHistoryCard from 'src/views/exams/ExamHistoryCard'

import {
  examStatusDisplayLabels,
  examTypeLabels,
  examTypeOptions,
  statusColors,
} from 'src/utils/constants'
import { buildGradcamDownloadName, buildOriginalDownloadName } from 'src/utils/examDownloadNames'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateBR, formatDateTimeBR } from 'src/utils/formatters'
import { getUserRole, hasPermission, PERMISSIONS, ROLES } from 'src/utils/permissions'

const allowedImageTypes = ['image/jpeg', 'image/png']
const analysisPollingIntervalMs = 2000
const maxConsecutivePollingErrors = 5

const examListFilterStatuses = new Set([
  'pending',
  'processing',
  'awaiting_review',
  'completed',
  'completed_with_divergence',
  'failed',
  'canceled',
])

const pendingImageAreaStyle = {
  display: 'block',
  height: 'auto',
}

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
  ai_analysis_status: 'not_processed',
  ai_summary: '',
  file_name: '',
  file_mime_type: '',
  findings: '',
  conclusion: '',
  reviewed_by_name: '',
  reviewed_at: '',
  analysis_in_progress: false,
  analysis_started_at: '',
}

const mergeExamSnapshot = (current, examData) => ({
  ...current,
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
  file_name: examData.file_name ?? '',
  file_mime_type: examData.file_mime_type ?? '',
  findings: examData.findings ?? '',
  conclusion: examData.conclusion ?? '',
  reviewed_by_name: examData.reviewed_by_name ?? '',
  reviewed_at: examData.reviewed_at ?? '',
  analysis_in_progress: Boolean(examData.analysis_in_progress),
  analysis_started_at: examData.analysis_started_at ?? '',
  ai_analysis_status: examData.ai_analysis_status ?? 'not_processed',
})

const resolveAiStatus = (form, analysis) => {
  if (analysis?.status_name) return analysis.status_name
  if (form.ai_analysis_status !== 'not_processed') return form.ai_analysis_status
  if (form.status_name === 'processing' && form.analysis_in_progress) return 'processing'
  if (form.status_name === 'failed') return 'failed'
  return 'not_processed'
}

const ExamForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const requestedPatientId = searchParams.get('patient')
  const { user } = useAuth()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyExam)
  const [clinics, setClinics] = useState([])
  const [patients, setPatients] = useState([])
  const [doctors, setDoctors] = useState([])
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [gradcamUrl, setGradcamUrl] = useState(null)
  const [gradcamError, setGradcamError] = useState('')
  const [isGradcamLoading, setIsGradcamLoading] = useState(false)
  const [isGradcamDownloading, setIsGradcamDownloading] = useState(false)
  const [originalImageUrl, setOriginalImageUrl] = useState(null)
  const [originalImageError, setOriginalImageError] = useState('')
  const [isOriginalImageLoading, setIsOriginalImageLoading] = useState(false)
  const [isOriginalDownloading, setIsOriginalDownloading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)

  const [review, setReview] = useState({
    findings: '',
    conclusion: '',
    has_discrepancy: false,
  })
  const [isReviewing, setIsReviewing] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'
  const isPendingView = isReadOnly && form.status_name === 'pending'

  const roleName = getUserRole(user)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isDoctor = roleName === ROLES.DOCTOR
  const canViewAiAnalysis =
    roleName !== ROLES.CLINIC_STAFF && hasPermission(user, PERMISSIONS.AI_ANALYSIS_READ)

  const canDownloadExamFile = !isCreateMode && hasPermission(user, PERMISSIONS.EXAMS_DOWNLOAD)

  // RN09: só médico registra a conclusão clínica. RN08: só faz sentido
  // revisar um exame que já está aguardando revisão médica — outros status
  // (processando, concluído, falhou, cancelado) não admitem essa ação.
  const canAnalyze =
    hasPermission(user, PERMISSIONS.AI_ANALYSIS_CREATE) &&
    !isCreateMode &&
    form.status_name === 'pending' &&
    !form.analysis_in_progress &&
    !aiAnalysis

  const canReview =
    isDoctor &&
    hasPermission(user, PERMISSIONS.EXAMS_REVIEW) &&
    !isCreateMode &&
    form.status_name === 'awaiting_review'

  const aiStatus = resolveAiStatus(form, aiAnalysis)
  const examListPath =
    !isCreateMode && examListFilterStatuses.has(form.status_name)
      ? `/exams?status=${form.status_name}`
      : '/exams'

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

  const authenticatedDoctorId = useMemo(() => {
    if (!isDoctor || doctors.length !== 1) return ''

    const [doctor] = doctors

    return doctor.status_name === 'active' ? String(doctor.id) : ''
  }, [doctors, isDoctor])

  const availablePatients = useMemo(() => {
    if (!form.clinic_id) return []

    return patients.filter(
      (patient) =>
        String(patient.clinic_id) === String(form.clinic_id) &&
        patient.status_name === 'active' &&
        (!isDoctor || String(patient.doctor_id) === authenticatedDoctorId),
    )
  }, [authenticatedDoctorId, form.clinic_id, isDoctor, patients])

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

        const defaultClinicId =
          loadedClinics.length === 1 && loadedClinics[0].status_name === 'active'
            ? String(loadedClinics[0].id)
            : ''

        const defaultDoctorId =
          isDoctor && loadedDoctors.length === 1 && loadedDoctors[0].status_name === 'active'
            ? String(loadedDoctors[0].id)
            : ''

        setClinics(loadedClinics)
        setPatients(loadedPatients)
        setDoctors(loadedDoctors)

        if (isCreateMode) {
          const requestedPatient = requestedPatientId
            ? loadedPatients.find(
                (patient) =>
                  String(patient.id) === requestedPatientId && patient.status_name === 'active',
              )
            : null

          const requestedClinic = requestedPatient
            ? loadedClinics.find(
                (clinic) =>
                  String(clinic.id) === String(requestedPatient.clinic_id) &&
                  clinic.status_name === 'active',
              )
            : null

          const requestedDoctor = requestedPatient
            ? loadedDoctors.find(
                (doctor) =>
                  String(doctor.id) === String(requestedPatient.doctor_id) &&
                  String(doctor.clinic_id) === String(requestedPatient.clinic_id) &&
                  doctor.status_name === 'active',
              )
            : null

          const canPreselectRequestedPatient = Boolean(
            requestedPatient && requestedClinic && requestedDoctor,
          )

          if (requestedPatientId && !canPreselectRequestedPatient) {
            showError(
              'O paciente, a clínica ou o médico responsável não está ativo ou disponível para este usuário.',
            )
          }

          setForm({
            ...emptyExam,
            clinic_id: canPreselectRequestedPatient ? String(requestedClinic.id) : defaultClinicId,
            patient_id: canPreselectRequestedPatient ? String(requestedPatient.id) : '',
            doctor_id: canPreselectRequestedPatient ? String(requestedDoctor.id) : defaultDoctorId,
          })

          setAiAnalysis(null)
          setGradcamUrl(null)
          return
        }

        const examData = await examService.getById(id)

        setForm((current) => mergeExamSnapshot(current, examData))

        // A análise só é consultada por perfis autorizados. A ausência de
        // análise (404) continua sendo tratada como um estado normal.
        const analysis = canViewAiAnalysis ? await aiAnalysisService.getByExamId(id) : null
        setAiAnalysis(analysis)

        // Reseta o formulário de revisão a cada carregamento, pra não
        // arrastar texto de uma revisão anterior (ex: usuário voltou à
        // tela depois de já ter revisado, ou trocou de exame).
        setReview({ findings: '', conclusion: '', has_discrepancy: false })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados do exame.'))
      } finally {
        setIsLoading(false)
      }
    }

    void loadData()
  }, [canViewAiAnalysis, id, isCreateMode, isDoctor, requestedPatientId, showError, showSuccess])

  const isAnalysisActive =
    !isCreateMode && form.status_name === 'processing' && form.analysis_in_progress && !aiAnalysis

  useEffect(() => {
    if (!isAnalysisActive) return undefined

    let isCancelled = false
    let timerId = null
    let consecutiveErrors = 0

    const scheduleNextPoll = () => {
      timerId = window.setTimeout(pollAnalysis, analysisPollingIntervalMs)
    }

    const pollAnalysis = async () => {
      try {
        const examData = await examService.getById(id)
        const analysis = canViewAiAnalysis ? await aiAnalysisService.getByExamId(id) : null

        if (isCancelled) return

        consecutiveErrors = 0
        setForm((current) => mergeExamSnapshot(current, examData))
        setAiAnalysis(analysis)
        setHistoryRefreshKey((current) => current + 1)

        const remainsActive =
          examData.status_name === 'processing' &&
          Boolean(examData.analysis_in_progress) &&
          !analysis

        if (remainsActive) {
          scheduleNextPoll()
        }
      } catch {
        consecutiveErrors += 1

        if (!isCancelled && consecutiveErrors < maxConsecutivePollingErrors) {
          scheduleNextPoll()
        }
      }
    }

    scheduleNextPoll()

    return () => {
      isCancelled = true
      if (timerId !== null) window.clearTimeout(timerId)
    }
  }, [canViewAiAnalysis, id, isAnalysisActive])

  // O Mapa Grad-CAM é carregado por uma rota de prévia.
  // Somente o clique explícito em download gera auditoria.
  useEffect(() => {
    if (!aiAnalysis?.gradcam_available || isCreateMode) {
      return undefined
    }

    let objectUrl = null
    let isCancelled = false

    const loadGradcam = async () => {
      try {
        setIsGradcamLoading(true)
        setGradcamError('')
        setGradcamUrl(null)

        const blob = await examService.previewAiFile(id)

        if (isCancelled) return

        objectUrl = URL.createObjectURL(blob)
        setGradcamUrl(objectUrl)
      } catch (err) {
        if (!isCancelled) {
          setGradcamUrl(null)
          setGradcamError(getErrorMessage(err, 'Não foi possível carregar o Mapa Grad-CAM.'))
        }
      } finally {
        if (!isCancelled) {
          setIsGradcamLoading(false)
        }
      }
    }

    void loadGradcam()

    return () => {
      isCancelled = true

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [aiAnalysis?.gradcam_available, id, isCreateMode])

  useEffect(() => {
    if (!canDownloadExamFile || !id) {
      return undefined
    }

    let objectUrl = null
    let isCancelled = false

    const loadOriginalImage = async () => {
      try {
        setIsOriginalImageLoading(true)
        setOriginalImageError('')
        setOriginalImageUrl(null)

        const blob = await examService.previewFile(id)

        if (isCancelled) return

        objectUrl = URL.createObjectURL(blob)
        setOriginalImageUrl(objectUrl)
      } catch (err) {
        if (!isCancelled) {
          setOriginalImageUrl(null)
          setOriginalImageError(
            getErrorMessage(err, 'Não foi possível carregar a imagem original.'),
          )
        }
      } finally {
        if (!isCancelled) {
          setIsOriginalImageLoading(false)
        }
      }
    }

    void loadOriginalImage()

    return () => {
      isCancelled = true

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [canDownloadExamFile, id])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleClinicChange = (clinicId) => {
    if (!isAdminMaster) return

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
      doctor_id: isDoctor
        ? authenticatedDoctorId
        : patient?.doctor_id
          ? String(patient.doctor_id)
          : '',
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

  const handleOriginalDownload = async () => {
    if (!canDownloadExamFile) return

    showError('')

    try {
      setIsOriginalDownloading(true)

      const blob = await examService.downloadFile(id)
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')

      anchor.href = objectUrl
      anchor.download = buildOriginalDownloadName({
        examId: id,
        patientName: selectedPatientName,
        examDate: form.exam_date,
        mimeType: blob.type || form.file_mime_type,
      })

      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()

      window.setTimeout(() => {
        URL.revokeObjectURL(objectUrl)
      }, 1000)
    } catch (err) {
      showError(getErrorMessage(err, 'Não foi possível baixar a imagem original.'))
    } finally {
      setIsOriginalDownloading(false)
    }
  }

  const handleGradcamDownload = async () => {
    if (!canViewAiAnalysis || !aiAnalysis?.gradcam_available) {
      return
    }

    showError('')

    try {
      setIsGradcamDownloading(true)

      const blob = await examService.downloadAiFile(id)
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')

      anchor.href = objectUrl
      anchor.download = buildGradcamDownloadName({
        examId: id,
        patientName: selectedPatientName,
        examDate: form.exam_date,
        mimeType: blob.type,
      })

      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()

      window.setTimeout(() => {
        URL.revokeObjectURL(objectUrl)
      }, 1000)
    } catch (err) {
      showError(getErrorMessage(err, 'Não foi possível baixar o Mapa Grad-CAM.'))
    } finally {
      setIsGradcamDownloading(false)
    }
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

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        const payload = buildCreatePayload()
        const createdExam = await examService.create(payload)
        showSuccess('Exame salvo com sucesso.')
        navigate(`/exams/${createdExam.id}`)
        return
      }

      if (isEditMode) {
        const payload = buildUpdatePayload()

        await examService.update(id, payload)
      }

      showSuccess('Exame salvo com sucesso.')
      navigate(`/exams/${id}`)
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar exame.'))
    } finally {
      setIsSaving(false)
    }
  }

  const handleAnalyze = async () => {
    if (!canAnalyze) return

    showError('')
    showSuccess('')
    try {
      setIsAnalyzing(true)
      setForm((current) => ({
        ...current,
        status_name: 'processing',
        status_display_name: examStatusDisplayLabels.processing,
        analysis_in_progress: true,
      }))
      const analysis = await examService.analyze(id)
      const updatedExam = await examService.getById(id)
      setAiAnalysis(analysis)
      setForm((current) => mergeExamSnapshot(current, updatedExam))
      setHistoryRefreshKey((current) => current + 1)
      showSuccess('Análise de IA concluída. O exame aguarda revisão médica.')
    } catch (err) {
      try {
        const updatedExam = await examService.getById(id)
        setForm((current) => mergeExamSnapshot(current, updatedExam))
        setHistoryRefreshKey((current) => current + 1)
      } catch {
        setForm((current) => ({ ...current, analysis_in_progress: false }))
      }
      showError(getErrorMessage(err, 'Erro ao executar a análise de IA.'))
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleReviewFieldChange = (field) => (event) => {
    setReview((prev) => ({ ...prev, [field]: event.target.value }))
  }

  const handleReviewSubmit = async (event) => {
    event.preventDefault()

    if (!canReview) return

    showError('')
    showSuccess('')

    if (review.findings.trim().length < 3 || review.conclusion.trim().length < 3) {
      showError('Preencha os achados e a conclusão antes de enviar a revisão.')
      return
    }

    try {
      setIsReviewing(true)

      const updatedExam = await examService.review(id, {
        findings: review.findings.trim(),
        conclusion: review.conclusion.trim(),
        has_discrepancy: review.has_discrepancy,
      })

      setForm((prev) => ({
        ...prev,
        status_id: updatedExam.status_id ? String(updatedExam.status_id) : prev.status_id,
        status_name: updatedExam.status_name ?? prev.status_name,
        status_display_name: updatedExam.status_display_name ?? prev.status_display_name,
        findings: updatedExam.findings ?? prev.findings,
        conclusion: updatedExam.conclusion ?? prev.conclusion,
        reviewed_by_name: updatedExam.reviewed_by_name ?? prev.reviewed_by_name,
        reviewed_at: updatedExam.reviewed_at ?? prev.reviewed_at,
      }))
      setHistoryRefreshKey((current) => current + 1)

      showSuccess(
        review.has_discrepancy
          ? 'Revisão registrada. Exame concluído com divergência sinalizada.'
          : 'Revisão registrada. Exame concluído, análise da IA confirmada.',
      )
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao registrar a revisão médica.'))
    } finally {
      setIsReviewing(false)
    }
  }

  const examDataCard = (
    <CCard>
      <CCardHeader>
        <strong>
          {isCreateMode ? 'Dados Cadastrais do Exame' : 'Dados Clínicos e Administrativos'}
        </strong>
      </CCardHeader>

      <CCardBody>
        <CForm onSubmit={handleSubmit}>
          <CRow className="g-3">
            <CCol md={6}>
              <CFormLabel>Clínica</CFormLabel>

              {isCreateMode && isAdminMaster ? (
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

              {isCreateMode && !isAdminMaster && (
                <div className="text-body-secondary small mt-1">
                  Clínica vinculada ao usuário autenticado.
                </div>
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
                    {form.clinic_id ? 'Selecione...' : 'Selecione uma clínica primeiro'}
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
                {isCreateMode && isDoctor
                  ? 'Médico autenticado responsável pelo exame.'
                  : 'O médico é definido automaticamente pelo paciente selecionado.'}
              </div>
            </CCol>

            <CCol md={6}>
              <CFormLabel>Status</CFormLabel>
              <CFormInput
                value={
                  examStatusDisplayLabels[form.status_name] ||
                  form.status_display_name ||
                  (isCreateMode ? 'Pendente após o cadastro' : '-')
                }
                disabled
              />
              <div className="text-body-secondary small mt-1">
                O status é controlado automaticamente pelo fluxo do sistema.
              </div>
            </CCol>

            <CCol md={12}>
              <CFormLabel>Título</CFormLabel>
              <CFormInput
                value={form.title}
                disabled={isReadOnly}
                placeholder="Identificador do exame. Ex: Colonoscopia - rastreamento"
                onChange={(event) => updateField('title', event.target.value)}
                required
              />
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

              {isReadOnly ? (
                <CFormInput value={formatDateBR(form.exam_date)} disabled />
              ) : (
                <CFormInput
                  type="date"
                  value={form.exam_date}
                  onChange={(event) => updateField('exam_date', event.target.value)}
                />
              )}
            </CCol>

            <CCol md={12}>
              <CFormLabel>Indicação clínica</CFormLabel>
              <CFormTextarea
                rows={2}
                value={form.clinical_indication}
                disabled={isReadOnly}
                placeholder="Motivo pelo qual o exame foi solicitado ou realizado. Ex: dor abdominal, rastreamento, refluxo persistente..."
                onChange={(event) => updateField('clinical_indication', event.target.value)}
              />
            </CCol>

            <CCol md={12}>
              <CFormLabel>Observações</CFormLabel>
              <CFormTextarea
                rows={2}
                value={form.description}
                disabled={isReadOnly}
                placeholder="Informações adicionais relacionadas ao cadastro do exame. Este campo não substitui os achados nem a conclusão médica."
                onChange={(event) => updateField('description', event.target.value)}
              />
            </CCol>

            {isCreateMode && (
              <CCol md={12}>
                <CFormLabel>Imagem do exame</CFormLabel>
                <CFormInput
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleFileChange}
                  required
                />
                <div className="text-body-secondary small mt-2">
                  Envie uma imagem em formato JPG, JPEG ou PNG.
                </div>
              </CCol>
            )}
          </CRow>

          {!isReadOnly && (
            <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
              <CButton color="primary" type="submit" disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Salvar'}
              </CButton>

              <CButton color="secondary" variant="outline" as={Link} to="/exams">
                Cancelar
              </CButton>
            </div>
          )}
        </CForm>
      </CCardBody>
    </CCard>
  )

  const examDataViewContent = (
    <CRow className="g-4">
      <CCol md={12}>
        <div className="text-body-secondary small mb-1">Paciente</div>
        <div className="fw-semibold">{selectedPatientName}</div>
      </CCol>

      <CCol md={6}>
        <div className="text-body-secondary small mb-1">Clínica</div>
        <div>{selectedClinicName}</div>
      </CCol>

      <CCol md={6}>
        <div className="text-body-secondary small mb-1">Médico responsável</div>
        <div>{selectedDoctorName}</div>
      </CCol>

      <CCol md={3}>
        <div className="text-body-secondary small mb-1">Data do exame</div>
        <div>{formatDateBR(form.exam_date)}</div>
      </CCol>

      <CCol md={3}>
        <div className="text-body-secondary small mb-1">Tipo de exame</div>
        <div>{examTypeLabels[form.exam_type] || form.exam_type || '-'}</div>
      </CCol>

      <CCol md={2}>
        <div className="text-body-secondary small mb-1">Status</div>
        <CBadge color={statusColors[form.status_name] || 'secondary'}>
          {examStatusDisplayLabels[form.status_name] || form.status_display_name || '-'}
        </CBadge>
      </CCol>

      <CCol xs={12}>
        <div className="text-body-secondary small mb-1">Indicação clínica</div>
        <div className="rounded bg-body-tertiary p-3">
          {form.clinical_indication?.trim() || 'Não informada.'}
        </div>
      </CCol>

      <CCol xs={12}>
        <div className="text-body-secondary small mb-1">Observações</div>
        <div className="rounded bg-body-tertiary p-3">
          {form.description?.trim() || 'Nenhuma observação registrada.'}
        </div>
      </CCol>
    </CRow>
  )

  const examDataViewCard = (
    <CCard>
      <CCardHeader>
        <strong>Dados do Exame</strong>
      </CCardHeader>

      <CCardBody>{examDataViewContent}</CCardBody>
    </CCard>
  )

  const pendingExamCard = (
    <CCard>
      <CCardHeader>
        <strong>Dados do Exame</strong>
      </CCardHeader>

      <CCardBody>
        <CRow className="g-4 align-items-start">
          <CCol lg={8}>{examDataViewContent}</CCol>

          <CCol lg={4}>
            <section aria-labelledby="pending-exam-image-title" className="w-100">
              <h2 id="pending-exam-image-title" className="h6 mb-3">
                Imagem do Exame
              </h2>

              {!canDownloadExamFile ? (
                <CAlert color="secondary" className="mb-0">
                  Você não possui permissão para acessar a imagem do exame.
                </CAlert>
              ) : isOriginalImageLoading ? (
                <div className="d-flex align-items-center justify-content-center gap-2 py-5 text-body-secondary">
                  <CSpinner size="sm" />
                  <span>Carregando imagem do exame...</span>
                </div>
              ) : originalImageUrl ? (
                <>
                  <div className="mb-3 text-center">
                    <img
                      src={originalImageUrl}
                      alt="Imagem original do exame"
                      className="w-100 rounded border"
                      style={pendingImageAreaStyle}
                    />
                  </div>

                  <div className="d-grid mt-3">
                    <CButton
                      color="primary"
                      onClick={handleOriginalDownload}
                      disabled={isOriginalDownloading}
                    >
                      {isOriginalDownloading ? (
                        <>
                          <CSpinner size="sm" className="me-2" />
                          Baixando...
                        </>
                      ) : (
                        'Baixar imagem do exame'
                      )}
                    </CButton>
                  </div>
                </>
              ) : (
                <CAlert color="warning" className="mb-0">
                  {originalImageError || 'Imagem do exame não disponível.'}
                </CAlert>
              )}
            </section>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>
  )

  return (
    <>
      <div className="d-flex flex-column flex-xl-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>

          <h1 className="h3 mb-0">{isCreateMode ? title : form.title || title}</h1>

          <p className="text-body-secondary mb-0">
            {isCreateMode
              ? 'Cadastre os dados e a imagem que serão vinculados ao exame.'
              : 'Consulte os dados do exame e acompanhe seu fluxo de análise e revisão.'}
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4 gap-2">
          {(canAnalyze || isAnalyzing) && (
            <CButton color="primary" size="lg" onClick={handleAnalyze} disabled={isAnalyzing}>
              {isAnalyzing ? (
                <>
                  <CSpinner size="sm" className="me-2" />
                  Analisando...
                </>
              ) : (
                'Executar Análise de IA'
              )}
            </CButton>
          )}

          <CButton color="secondary" size="lg" variant="outline" as={Link} to={examListPath}>
            Voltar
          </CButton>
        </div>
      </div>

      {isPendingView ? (
        <>
          {pendingExamCard}

          <ExamHistoryCard
            examId={id}
            refreshKey={historyRefreshKey}
            collapsible
            defaultOpen={false}
          />
        </>
      ) : !isCreateMode ? (
        <>
          <CRow className="g-4">
            {(canReview || form.findings || form.conclusion) && (
              <CCol xs={12}>
                <div id="revisao-medica">
                  {canReview ? (
                    <CCard className="border-warning">
                      <CCardHeader className="bg-warning-subtle">
                        <strong>Revisão médica</strong>
                      </CCardHeader>

                      <CCardBody>
                        <CAlert color="warning" className="small">
                          Antes de concluir, compare a imagem original, o Mapa Grad-CAM e o
                          resultado automatizado apresentados abaixo. Os achados e a conclusão
                          encerram o exame.
                        </CAlert>

                        <CForm onSubmit={handleReviewSubmit}>
                          <div className="mb-3">
                            <CFormLabel htmlFor="findings">Achados da revisão médica *</CFormLabel>
                            <CFormTextarea
                              id="findings"
                              rows={4}
                              value={review.findings}
                              onChange={handleReviewFieldChange('findings')}
                              placeholder="Descreva os achados observados ao interpretar a imagem e o resultado automatizado."
                              required
                            />
                          </div>

                          <div className="mb-3">
                            <CFormLabel htmlFor="conclusion">Conclusão médica *</CFormLabel>
                            <CFormTextarea
                              id="conclusion"
                              rows={4}
                              value={review.conclusion}
                              onChange={handleReviewFieldChange('conclusion')}
                              placeholder="Registre o parecer final sobre o exame."
                              required
                            />
                          </div>

                          <div className="mb-3">
                            <CFormLabel>Em relação à classificação automatizada</CFormLabel>

                            <CFormCheck
                              type="radio"
                              name="has_discrepancy"
                              id="discrepancy-false"
                              label="Confirmo o resultado sugerido pela IA"
                              checked={!review.has_discrepancy}
                              onChange={() =>
                                setReview((current) => ({
                                  ...current,
                                  has_discrepancy: false,
                                }))
                              }
                            />

                            <CFormCheck
                              type="radio"
                              name="has_discrepancy"
                              id="discrepancy-true"
                              label="Identifiquei divergência em relação ao resultado da IA"
                              checked={review.has_discrepancy}
                              onChange={() =>
                                setReview((current) => ({
                                  ...current,
                                  has_discrepancy: true,
                                }))
                              }
                            />
                          </div>

                          <CButton type="submit" color="warning" disabled={isReviewing}>
                            {isReviewing ? (
                              <>
                                <CSpinner size="sm" className="me-2" />
                                Registrando revisão...
                              </>
                            ) : (
                              'Concluir revisão'
                            )}
                          </CButton>
                        </CForm>
                      </CCardBody>
                    </CCard>
                  ) : (
                    <CCard
                      className={
                        form.status_name === 'completed_with_divergence'
                          ? 'border-dark'
                          : 'border-success'
                      }
                    >
                      <CCardHeader>
                        <strong>Resultado da revisão médica</strong>
                      </CCardHeader>

                      <CCardBody>
                        <div className="mb-3">
                          <div className="text-body-secondary small">Achados da revisão médica</div>
                          <div>{form.findings || '-'}</div>
                        </div>

                        <div className="mb-3">
                          <div className="text-body-secondary small">Conclusão médica</div>
                          <div>{form.conclusion || '-'}</div>
                        </div>

                        <div className="mb-3">
                          <div className="text-body-secondary small">Desfecho</div>
                          <CBadge
                            color={
                              form.status_name === 'completed_with_divergence' ? 'dark' : 'success'
                            }
                          >
                            {form.status_name === 'completed_with_divergence'
                              ? 'Concluído com divergência'
                              : 'Concluído'}
                          </CBadge>
                        </div>

                        <div>
                          <div className="text-body-secondary small">Revisado por</div>
                          <div>
                            {form.reviewed_by_name || '-'}
                            {form.reviewed_at ? ` em ${formatDateTimeBR(form.reviewed_at)}` : ''}
                          </div>
                        </div>
                      </CCardBody>
                    </CCard>
                  )}
                </div>
              </CCol>
            )}

            <CCol xs={12}>
              <ExamAiResultCard
                aiStatus={aiStatus}
                aiAnalysis={aiAnalysis}
                canViewAiAnalysis={canViewAiAnalysis}
                canDownloadExamFile={canDownloadExamFile}
                originalImageUrl={originalImageUrl}
                originalImageError={originalImageError}
                isOriginalImageLoading={isOriginalImageLoading}
                isOriginalDownloading={isOriginalDownloading}
                onOriginalDownload={handleOriginalDownload}
                gradcamUrl={gradcamUrl}
                gradcamError={gradcamError}
                isGradcamLoading={isGradcamLoading}
                isGradcamDownloading={isGradcamDownloading}
                onGradcamDownload={handleGradcamDownload}
              />
            </CCol>
          </CRow>

          <div className="mt-4">{isReadOnly ? examDataViewCard : examDataCard}</div>

          <ExamHistoryCard
            examId={id}
            refreshKey={historyRefreshKey}
            collapsible={isReadOnly}
            defaultOpen={!isReadOnly}
          />
        </>
      ) : (
        <CRow className="g-4">
          <CCol lg={12}>{examDataCard}</CCol>
        </CRow>
      )}
    </>
  )
}

export default ExamForm
