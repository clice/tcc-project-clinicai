/**
 * Formulário do módulo de Permission usando mocks.
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

import { permissions as permissionsMock } from 'src/mocks/data'

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
  { value: 'exams', label: 'Exames' },
  { value: 'roles', label: 'Perfis' },
  { value: 'permissions', label: 'Permissões' },
  { value: 'statuses', label: 'Status' },
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

    const foundPermission = permissionsMock.find(
      (permission) => String(permission.id) === String(id),
    )

    if (!foundPermission) {
      setError('Permissão não encontrada no mock.')
      setIsLoading(false)
      return
    }

    setForm({
      name: foundPermission.name ?? '',
      display_name: foundPermission.display_name ?? '',
      description: foundPermission.description ?? '',
      module: foundPermission.module ?? '',
    })

    setIsLoading(false)
  }, [id, isCreateMode])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const normalizePermissionName = (value) => {
    return value
      .trim()
      .toLowerCase()
      .replace(/\s+/g, ':')
      .replace(/\.+/g, ':')
      .replace(/:+/g, ':')
      .replace(/[^a-z0-9:_-]/g, '')
  }

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

    const normalizedName = normalizePermissionName(form.name)

    const duplicated = permissionsMock.some((permission) => {
      const isSamePermission = String(permission.id) === String(id)

      return !isSamePermission && permission.name === normalizedName
    })

    if (duplicated) {
      return 'Já existe uma permissão com esse nome técnico.'
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

      console.log('Payload mock de permissão:', payload)

      if (isCreateMode) {
        setSuccess('Permissão cadastrada com sucesso no mock.')
        navigate('/permissions')
        return
      }

      if (isEditMode) {
        setSuccess('Permissão atualizada com sucesso no mock.')
      }
    } catch (err) {
      setError(err.message || 'Erro ao salvar a permissão.')
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

        <CButton color="secondary" size="lg" variant="outline" as={Link} to="/permissions">
          Voltar
        </CButton>
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