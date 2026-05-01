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

import { statuses as statusesMock } from 'src/mocks/data'

const emptyStatus = {
  name: '',
  display_name: '',
  applies_to: '',
  description: '',
}

const appliesToOptions = [
  { value: '', label: 'Selecione uma entidade' },
  { value: 'users', label: 'Usuários' },
  { value: 'clinics', label: 'Clínicas' },
  { value: 'patients', label: 'Pacientes' },
  { value: 'exams', label: 'Exames' },
]

const StatusForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyStatus)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(mode !== 'create')
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const title = useMemo(() => {
    if (mode === 'create') return 'Cadastrar Status'
    if (mode === 'edit') return 'Editar Status'
    return 'Detalhes do Status'
  }, [mode])

  useEffect(() => {
    if (isCreateMode) {
      setIsLoading(false)
      return
    }

    const found = statusesMock.find((status) => String(status.id) === String(id))

    if (!found) {
      setError('Status não encontrado no mock.')
      setIsLoading(false)
      return
    }

    setForm({
      name: found.name ?? '',
      display_name: found.display_name ?? '',
      applies_to: found.applies_to ?? '',
      description: found.description ?? '',
    })

    setIsLoading(false)
  }, [id, isCreateMode])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const normalizeName = (value) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  }

  const buildPayload = () => ({
    name: form.name.trim(),
    display_name: form.display_name.trim(),
    applies_to: form.applies_to.trim(),
    description: form.description.trim() || null,
  })

  const validateForm = () => {
    if (!form.name.trim()) return 'Informe o nome técnico do status.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'
    if (!form.applies_to.trim()) return 'Informe onde esse status será aplicado.'

    const duplicated = statusesMock.some((status) => {
      const isSameStatus = String(status.id) === String(id)

      return (
        !isSameStatus &&
        status.name === form.name.trim() &&
        status.applies_to === form.applies_to.trim()
      )
    })

    if (duplicated) {
      return 'Já existe um status com esse nome técnico para essa entidade.'
    }

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    setError('')
    setSuccess('')

    const validationError = validateForm()

    if (validationError) {
      setError(validationError)
      return
    }

    try {
      setIsSaving(true)

      const payload = buildPayload()

      console.log('Payload mock de status:', payload)

      if (isCreateMode) {
        setSuccess('Status cadastrado com sucesso no mock.')
        navigate('/statuses')
        return
      }

      if (isEditMode) {
        setSuccess('Status atualizado com sucesso no mock.')
      }
    } catch (err) {
      setError(err.message || 'Erro ao salvar status.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Administração</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            Status centralizados por entidade do sistema.
          </p>
        </div>

        <CButton color="secondary" size="lg" variant="outline" as={Link} to="/statuses">
          Voltar
        </CButton>
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados do Status</strong>
        </CCardHeader>

        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}
          {success && <CAlert color="success">{success}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando status...</p>
          ) : (
            <CForm onSubmit={handleSubmit}>
              <CRow className="g-3">
                <CCol md={4}>
                  <CFormLabel>Nome Técnico</CFormLabel>
                  <CFormInput
                    value={form.name}
                    disabled={isReadOnly}
                    placeholder="Ex: active, inactive, processing"
                    onChange={(e) => updateField('name', normalizeName(e.target.value))}
                    required
                  />
                </CCol>

                <CCol md={4}>
                  <CFormLabel>Nome de Exibição</CFormLabel>
                  <CFormInput
                    value={form.display_name}
                    disabled={isReadOnly}
                    placeholder="Ex: Ativo, Inativo, Em processamento"
                    onChange={(e) => updateField('display_name', e.target.value)}
                    required
                  />
                </CCol>

                <CCol md={4}>
                  <CFormLabel>Aplicado em</CFormLabel>
                  <CFormSelect
                    value={form.applies_to}
                    disabled={isReadOnly}
                    onChange={(e) => updateField('applies_to', e.target.value)}
                    required
                  >
                    {appliesToOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>

                <CCol md={12}>
                  <CFormLabel>Descrição</CFormLabel>
                  <CFormInput
                    value={form.description}
                    disabled={isReadOnly}
                    placeholder="Descreva quando esse status deve ser usado"
                    onChange={(e) => updateField('description', e.target.value)}
                  />
                </CCol>
              </CRow>

              {!isReadOnly && (
                <CButtonGroup className="mt-4">
                  <CButton color="primary" type="submit" disabled={isSaving}>
                    {isSaving ? 'Salvando...' : 'Salvar'}
                  </CButton>

                  <CButton color="secondary" variant="outline" as={Link} to="/statuses">
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

export default StatusForm