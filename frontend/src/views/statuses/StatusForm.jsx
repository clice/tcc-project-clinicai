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

import { useFeedback } from 'src/hooks/useFeedback'

import { statusService } from 'src/services/statusService'

import { statusNameOptions, statusScopeOptions } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'

const emptyStatus = {
  name: '',
  display_name: '',
  applies_to: '',
  description: '',
}

const StatusForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyStatus)
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
      stopLoading()
      return
    }

    const loadStatus = async () => {
      try {
        startLoading()
        showError('')

        const statusData = await statusService.getById(id)

        setForm({
          name: statusData.name ?? '',
          display_name: statusData.display_name ?? '',
          applies_to: statusData.applies_to ?? '',
          description: statusData.description ?? '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar o status.'))
      } finally {
        stopLoading()
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
   * Monta o payload enviado para a API.
   */
  const buildPayload = () => ({
    name: form.name,
    display_name: form.display_name.trim(),
    applies_to: form.applies_to,
    description: form.description.trim() || null,
  })

  /**
   * Valida os campos do formulário antes de enviar para a API.
   */
  const validateForm = () => {
    if (!form.name) return 'Selecione o nome técnico do status.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'
    if (!form.applies_to) return 'Selecione onde esse status será aplicado.'

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    showError('')
    showSuccess('')

    const validationError = validateForm()

    if (validationError) {
      showError(validationError)
      return
    }

    try {
      setIsSaving(true)

      if (isCreateMode) {
        const created = await statusService.create(buildPayload())

        if (created?.id) {
          navigate(`/statuses/${created.id}/edit`)
          showSuccess('Status cadastrado com sucesso.')
          return
        }

        navigate('/statuses')
        return
      }

      if (isEditMode) {
        await statusService.update(id, buildPayload())
        showSuccess('Status atualizado com sucesso.')
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar usuário.'))
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
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormLabel>Nome Técnico</CFormLabel>
                <CFormSelect
                  value={form.name}
                  disabled={isReadOnly}
                  onChange={(e) => updateField('name', e.target.value)}
                  required
                >
                  <option value="">Selecione...</option>
                  {statusNameOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </CFormSelect>
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
                  <option value="">Selecione...</option>
                  {statusScopeOptions.map((option) => (
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
        </CCardBody>
      </CCard>
    </>
  )
}

export default StatusForm