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

import { permissionService } from 'src/services/permissionService'

const emptyPermission = {
  name: '',
  display_name: '',
  description: '',
  module: '',
}

const moduleOptions = [
  { value: 'users', label: 'Usuários' },
  { value: 'clinics', label: 'Clínicas' },
  { value: 'patients', label: 'Pacientes' },
  { value: 'ai_analysis', label: 'Análises IA' },
  { value: 'exams', label: 'Exames' },
  { value: 'roles', label: 'Perfis' },
  { value: 'permissions', label: 'Permissões' },
  { value: 'statuses', label: 'Status' },
  { value: 'audit_logs', label: 'Logs de Auditoria' },
]

const PermissionForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyPermission)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(mode !== 'create')
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Permissão'
    if (isEditMode) return 'Editar Permissão'
    return 'Detalhes da Permissão'
  }, [isCreateMode, isEditMode])

  useEffect(() => {
    if (isCreateMode) {
      setIsLoading(false)
      return
    }

    const loadPermission = async () => {
      try {
        setIsLoading(true)
        setError('')

        const permissionData = await permissionService.getById(id)

        setForm({
          name: permissionData.name ?? '',
          display_name: permissionData.display_name ?? '',
          description: permissionData.description ?? '',
          module: permissionData.module ?? '',
        })
      } catch (err) {
        setError(err.response?.data?.detail || 'Erro ao carregar a permissão.')
      } finally {
        setIsLoading(false)
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
  const normalizePermissionName = (value) => {
    return value
      .trim()
      .toLowerCase()
      .replace(/\s+/g, ':')
      .replace(/\.+/g, ':')
      .replace(/:+/g, ':')
      .replace(/[^a-z0-9:_-]/g, '')
  }

  /**
   * Monta o payload enviado para a API.
   */
  const buildPayload = () => ({
    name: normalizePermissionName(form.name),
    display_name: form.display_name.trim(),
    description: form.description.trim() || null,
    module: form.module.trim(),
  })

  const validateForm = () => {
    if (!form.name.trim()) return 'Informe o nome técnico da permissão.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição.'
    if (!form.module.trim()) return 'Informe o módulo da permissão.'

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

      setIsSaving(true)

      if (isCreateMode) {
        const created = await permissionService.create(buildPayload())

        if (created?.id) {
          navigate(`/permissions/${created.id}/edit`)
          return
        }

        navigate('/permissions')
        return
      }

      if (isEditMode) {
        await permissionService.update(id, buildPayload())
        setSuccess('Permissão atualizada com sucesso.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao salvar a permissão.')
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
          {error && <CAlert color="danger">{error}</CAlert>}
          {success && <CAlert color="success">{success}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando permissão...</p>
          ) : (
            <CForm onSubmit={handleSubmit}>
              <CRow className="g-3">
                <CCol md={6}>
                  <CFormLabel>Nome técnico</CFormLabel>
                  <CFormInput
                    value={form.name}
                    disabled={isReadOnly}
                    placeholder="Ex: users:create"
                    onChange={(event) =>
                      updateField('name', normalizePermissionName(event.target.value))
                    }
                    required
                  />
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Nome de exibição</CFormLabel>
                  <CFormInput
                    value={form.display_name}
                    disabled={isReadOnly}
                    placeholder="Ex: Criar Usuários"
                    onChange={(event) =>
                      updateField('display_name', event.target.value)
                    }
                    required
                  />
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Descrição</CFormLabel>
                  <CFormInput
                    value={form.description}
                    disabled={isReadOnly}
                    placeholder="Ex: Permite cadastrar novos usuários no sistema."
                    onChange={(event) =>
                      updateField('description', event.target.value)
                    }
                  />
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Módulo</CFormLabel>
                  <CFormSelect
                    value={form.module}
                    disabled={isReadOnly}
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
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default PermissionForm