/**
 * Edição dos textos de apresentação de um status oficial.
 *
 * Nome técnico e entidade de aplicação pertencem ao catálogo fechado.
 */

import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CRow,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'

import { statusService } from 'src/services/statusService'

import { getErrorMessage } from 'src/utils/errors'

const emptyStatus = {
  name: '',
  display_name: '',
  applies_to: '',
  description: '',
}

const StatusForm = () => {
  const { id } = useParams()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyStatus)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
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

    void loadStatus()
  }, [id, showError, startLoading, stopLoading])

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
   * Monta o payload editável enviado para a API.
   * Nome técnico e escopo pertencem ao catálogo fechado e não são enviados.
   */
  const buildPayload = () => ({
    display_name: form.display_name.trim(),
    description: form.description.trim() || null,
  })

  /**
   * Valida os campos do formulário antes de enviar para a API.
   */
  const validateForm = () => {
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    showError('')
    showSuccess('')

    const validationError = validateForm()

    if (validationError) {
      showError(validationError)
      return
    }

    try {
      setIsSaving(true)

      await statusService.update(id, buildPayload())
      showSuccess('Status atualizado com sucesso.')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar status.'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Administração</div>
          <h1 className="h3 mb-0 clinicai-page-title">Editar Status</h1>
          <p className="text-body-secondary mb-0">Status centralizados por entidade do sistema.</p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton
            color="secondary"
            size="lg"
            variant="outline"
            className="clinicai-soft-action"
            as={Link}
            to="/statuses"
          >
            Voltar
          </CButton>
        </div>
      </div>

      <div className="alert alert-info">
        Esta tela permite alterar os textos de apresentação do status. Revise as informações antes
        de selecionar “Salvar”.
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados do Status</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormLabel>Nome técnico</CFormLabel>
                <CFormInput value={form.name} disabled readOnly />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Nome de exibição</CFormLabel>
                <CFormInput
                  value={form.display_name}
                  placeholder="Ex: Ativo, Inativo, Em processamento"
                  onChange={(e) => updateField('display_name', e.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Aplicado em</CFormLabel>
                <CFormInput value={form.applies_to} disabled readOnly />
                <div className="form-text">
                  Nome técnico e escopo definidos pelo catálogo oficial do sistema.
                </div>
              </CCol>

              <CCol md={12}>
                <CFormLabel>Descrição</CFormLabel>
                <CFormInput
                  value={form.description}
                  placeholder="Descreva quando esse status deve ser usado"
                  onChange={(e) => updateField('description', e.target.value)}
                />
              </CCol>
            </CRow>

            <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
              <CButton color="primary" type="submit" disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Salvar'}
              </CButton>

              <CButton color="secondary" variant="outline" as={Link} to="/statuses">
                Cancelar
              </CButton>
            </div>
          </CForm>
        </CCardBody>
      </CCard>
    </>
  )
}

export default StatusForm
