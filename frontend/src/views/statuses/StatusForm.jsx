/**
 * Formulário do módulo de Status.
 *
 * Usado para:
 * - criar status;
 * - visualizar status;
 * - editar status.
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
  CRow,
} from '@coreui/react'

import { statusService } from 'src/services/statusService'

const emptyStatus = {
  name: '',
  display_name: '',
  applies_to: '',
  description: '',
}

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
    if (isCreateMode) return 'Cadastrar Status'
    if (isEditMode) return 'Editar Status'
    return 'Detalhes do Status'
  }, [isCreateMode, isEditMode])

  useEffect(() => {
    if (isCreateMode) {
      setIsLoading(false)
      return
    }

    const loadStatus = async () => {
      try {
        setIsLoading(true)
        setError('')

        const statusData = await statusService.getById(id)

        setForm({
          name: statusData.name ?? '',
          display_name: statusData.display_name ?? '',
          applies_to: statusData.applies_to ?? '',
          description: statusData.description ?? '',
        })
      } catch (err) {
        setError(err.response?.data?.detail || 'Erro ao carregar o status.')
      } finally {
        setIsLoading(false)
      }
    }

    loadStatus()
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

  /**
   * Normaliza campos técnicos para o padrão usado no backend.
   */
  const normalizeName = (value) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  }

  /**
   * Monta o payload enviado para a API.
   */
  const buildPayload = () => ({
    name: normalizeName(form.name),
    display_name: form.display_name.trim(),
    applies_to: normalizeName(form.applies_to),
    description: form.description.trim() || null,
  })

  /**
   * Valida os campos do formulário antes de enviar para a API.
   */
  const validateForm = () => {
    if (!form.name.trim()) return 'Informe o nome técnico do status.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'
    if (!form.applies_to.trim()) return 'Informe onde esse status será aplicado.'

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

      if (isCreateMode) {
        const created = await statusService.create(buildPayload())

        if (created?.id) {
          navigate(`/statuses/${created.id}/edit`)
          return
        }

        navigate('/statuses')
        return
      }

      if (isEditMode) {
        await statusService.update(id, buildPayload())
        setSuccess('Status atualizado com sucesso.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao salvar o status.')
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

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/statuses">
            Voltar
          </CButton>
        </div>
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
                  <CFormInput
                    value={form.applies_to}
                    disabled={isReadOnly}
                    placeholder="Ex: user, clinic, patient"
                    onChange={(e) => updateField('applies_to', e.target.value)}
                    required
                  />
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