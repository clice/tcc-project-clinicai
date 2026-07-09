/**
 * Formulário do módulo de Permission.
 *
 * Usado para:
 * - criar permissão;
 * - visualizar permissão;
 * - editar permissão.
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

import { permissionService } from 'src/services/permissionService'

import { actionOptions, moduleOptions } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'

const emptyPermission = {
  module: '',
  action: '',
  display_name: '',
  description: '',
}

const splitPermissionName = (name = '') => {
  const [module = '', action = ''] = String(name).split(':')
  return { module, action }
}

const PermissionForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyPermission)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const permissionName = useMemo(() => {
    if (!form.module || !form.action) return ''
    return `${form.module}:${form.action}`
  }, [form.module, form.action])

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Permissão'
    if (isEditMode) return 'Editar Permissão'
    return 'Detalhes da Permissão'
  }, [isCreateMode, isEditMode])

  useEffect(() => {
    if (isCreateMode) {
      stopLoading()
      return
    }

    const loadPermission = async () => {
      try {
        startLoading()
        showError('')

        const permissionData = await permissionService.getById(id)
        const parsedName = splitPermissionName(permissionData.name)

        setForm({
          module: permissionData.module || parsedName.module || '',
          action: parsedName.action || '',
          display_name: permissionData.display_name ?? '',
          description: permissionData.description ?? '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar a permissão.'))
      } finally {
        stopLoading()
      }
    }

    void loadPermission()
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
  const normalizePermissionName = (value = '') => {
    return String(value)
      .trim()
      .toLowerCase()
      .replace(/\s+/g, ':')
      .replace(/\.+/g, ':')
      .replace(/:+/g, ':')
      .replace(/[^a-z0-9:_-]/g, '')
  }

  /**
   * Monta o payload enviado para a API.
   * name e module só são enviados na criação — são imutáveis na edição
   * (o backend nem aceita mais o campo name em PermissionUpdate).
   */
  const buildPayload = () => {
    if (isEditMode) {
      return {
        display_name: form.display_name.trim(),
        description: form.description.trim() || null,
      }
    }

    return {
      name: normalizePermissionName(permissionName),
      display_name: form.display_name.trim(),
      description: form.description.trim() || null,
      module: form.module.trim(),
    }
  }

  const validateForm = () => {
    if (!form.module) return 'Selecione o módulo da permissão.'
    if (!form.action) return 'Selecione a ação da permissão.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'

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
        const created = await permissionService.create(buildPayload())
        navigate(created?.id ? `/permissions/${created.id}` : '/permissions')
        return
      }

      if (isEditMode) {
        await permissionService.update(id, buildPayload())
        showSuccess('Permissão atualizada com sucesso.')
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar a permissão.'))
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
            Permissões controlam o acesso às funcionalidades do sistema.
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
          <strong>Registro da Permissão</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormLabel>Módulo</CFormLabel>
                <CFormSelect
                  value={form.module}
                  disabled={isReadOnly || isEditMode}
                  onChange={(event) => updateField('module', event.target.value)}
                  required
                >
                  <option value="">Selecione...</option>
                  {moduleOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={4}>
                <CFormLabel>Ação</CFormLabel>
                <CFormSelect
                  value={form.action}
                  disabled={isReadOnly || isEditMode}
                  onChange={(event) => updateField('action', event.target.value)}
                  required
                >
                  <option value="">Selecione...</option>
                  {actionOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={4}>
                <CFormLabel>Nome técnico</CFormLabel>
                <CFormInput value={permissionName} disabled readOnly placeholder="modulo:acao" />
                {isEditMode && (
                  <div className="form-text">
                    Módulo, ação e nome técnico não podem ser alterados após a criação.
                  </div>
                )}
              </CCol>

              <CCol md={6}>
                <CFormLabel>Nome de exibição</CFormLabel>
                <CFormInput
                  value={form.display_name}
                  disabled={isReadOnly}
                  placeholder="Ex: Criar Usuários"
                  onChange={(event) => updateField('display_name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Descrição</CFormLabel>
                <CFormInput
                  value={form.description}
                  disabled={isReadOnly}
                  placeholder="Ex: Permite cadastrar novos usuários no sistema."
                  onChange={(event) => updateField('description', event.target.value)}
                />
              </CCol>
            </CRow>

            {!isReadOnly && (
              <CButtonGroup className="mt-4">
                <CButton color="primary" type="submit" disabled={isSaving}>
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </CButton>

                <CButton color="secondary" variant="outline" as={Link} to="/permissions">
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

export default PermissionForm