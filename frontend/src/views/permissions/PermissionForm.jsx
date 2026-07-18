/**
 * Visualização e edição dos textos de uma permissão oficial.
 *
 * Nome técnico, módulo e ação pertencem ao catálogo versionado e são sempre
 * somente leitura. Novas permissões são introduzidas por código e migration.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
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
  CRow,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'
import { permissionService } from 'src/services/permissionService'
import { moduleLabels } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'

const emptyPermission = {
  name: '',
  module: '',
  action: '',
  display_name: '',
  description: '',
}

const PermissionForm = ({ mode = 'view' }) => {
  const { id } = useParams()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyPermission)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isEditMode = mode === 'edit'
  const title = useMemo(
    () => (isEditMode ? 'Editar Permissão' : 'Detalhes da Permissão'),
    [isEditMode],
  )

  useEffect(() => {
    const loadPermission = async () => {
      try {
        startLoading()
        showError('')

        const permission = await permissionService.getById(id)
        const [, action = ''] = String(permission.name || '').split(':')

        setForm({
          name: permission.name || '',
          module: permission.module || '',
          action,
          display_name: permission.display_name ?? '',
          description: permission.description ?? '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar a permissão.'))
      } finally {
        stopLoading()
      }
    }

    void loadPermission()
  }, [id, showError, startLoading, stopLoading])

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!isEditMode) return

    showError('')
    showSuccess('')

    if (!form.display_name.trim()) {
      showError('Informe o nome de exibição.')
      return
    }

    try {
      setIsSaving(true)
      await permissionService.update(id, {
        display_name: form.display_name.trim(),
        description: form.description.trim() || null,
      })
      showSuccess('Permissão atualizada com sucesso.')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao atualizar a permissão.'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Configurações</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            O catálogo técnico é versionado; apenas os textos de apresentação podem ser editados.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/permissions">
            Voltar
          </CButton>
        </div>
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados da Permissão</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormLabel>Módulo</CFormLabel>
                <CFormInput value={moduleLabels[form.module] || form.module} disabled readOnly />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Ação</CFormLabel>
                <CFormInput value={form.action} disabled readOnly />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Nome técnico</CFormLabel>
                <CFormInput value={form.name} disabled readOnly />
                <div className="form-text">
                  Alterações técnicas exigem código, migration e teste de rota.
                </div>
              </CCol>

              <CCol md={6}>
                <CFormLabel>Nome de exibição</CFormLabel>
                <CFormInput
                  value={form.display_name}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('display_name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Descrição</CFormLabel>
                <CFormInput
                  value={form.description}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('description', event.target.value)}
                />
              </CCol>
            </CRow>

            {!isReadOnly && (
              <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
                <CButton
                  color="primary"
                  type="submit"
                  disabled={isSaving}
                >
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </CButton>
  
                <CButton
                  color="secondary"
                  variant="outline"
                  as={Link}
                  to="/exams"
                >
                  Cancelar
                </CButton>
              </div>
            )}
          </CForm>
        </CCardBody>
      </CCard>
    </>
  )
}

export default PermissionForm
