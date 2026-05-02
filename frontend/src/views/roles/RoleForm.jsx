/**
 * Formulário do módulo de Roles usando mocks.
 *
 * Usado para:
 * - criar perfil;
 * - visualizar perfil;
 * - editar perfil;
 * - vincular permissões ao perfil usando checkboxes.
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
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormTextarea,
  CRow,
} from '@coreui/react'

import {
  permissions as permissionsMock,
  roles as rolesMock,
  rolePermissions as rolePermissionsMock,
} from 'src/mocks/data'

const emptyRole = {
  name: '',
  display_name: '',
  description: '',
}

const moduleLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
  roles: 'Perfis',
  permissions: 'Permissões',
  statuses: 'Status',
}

const RoleForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyRole)
  const [permissions, setPermissions] = useState([])
  const [selectedPermissionIds, setSelectedPermissionIds] = useState([])

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Perfil'
    if (isEditMode) return 'Editar Perfil'
    return 'Detalhes do Perfil'
  }, [isCreateMode, isEditMode])

  const groupedPermissions = useMemo(() => {
    return permissions.reduce((groups, permission) => {
      const moduleName = permission.module || 'other'

      if (!groups[moduleName]) {
        groups[moduleName] = []
      }

      groups[moduleName].push(permission)

      return groups
    }, {})
  }, [permissions])

  useEffect(() => {
    setIsLoading(true)
    setError('')

    setPermissions(Array.isArray(permissionsMock) ? permissionsMock : [])

    if (isCreateMode) {
      setIsLoading(false)
      return
    }

    const foundRole = rolesMock.find((role) => String(role.id) === String(id))

    if (!foundRole) {
      setError('Perfil não encontrado no mock.')
      setIsLoading(false)
      return
    }

    const linkedPermissions = rolePermissionsMock.find(
      (item) => String(item.role_id) === String(id),
    )

    setForm({
      name: foundRole.name ?? '',
      display_name: foundRole.display_name ?? '',
      description: foundRole.description ?? '',
    })

    setSelectedPermissionIds(
      linkedPermissions?.permission_ids?.map((permissionId) => Number(permissionId)) ?? [],
    )

    setIsLoading(false)
  }, [id, isCreateMode])

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const normalizeSlug = (value) => {
    return value
      .trim()
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  }

  const togglePermission = (permissionId) => {
    setSelectedPermissionIds((current) => {
      const numericId = Number(permissionId)

      if (current.includes(numericId)) {
        return current.filter((id) => id !== numericId)
      }

      return [...current, numericId]
    })
  }

  const buildPayload = () => ({
    name: normalizeSlug(form.name),
    display_name: form.display_name.trim(),
    description: form.description.trim() || null,
    permission_ids: selectedPermissionIds,
  })

  const validateForm = () => {
    if (!form.name.trim()) return 'Informe o nome técnico do perfil.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição do perfil.'

    const normalizedName = normalizeSlug(form.name)

    const duplicated = rolesMock.some((role) => {
      const isSameRole = String(role.id) === String(id)

      return !isSameRole && role.name === normalizedName
    })

    if (duplicated) {
      return 'Já existe um perfil com esse nome técnico.'
    }

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    setIsSaving(true)
    setError('')
    setSuccess('')

    const validationError = validateForm()

    if (validationError) {
      setError(validationError)
      setIsSaving(false)
      return
    }

    try {
      const payload = buildPayload()

      console.log('Payload mock de role:', payload)

      if (isCreateMode) {
        setSuccess('Perfil cadastrado com sucesso no mock.')
        navigate('/roles')
        return
      }

      if (isEditMode) {
        setSuccess('Perfil atualizado com sucesso no mock.')
      }
    } catch (err) {
      setError(err.message || 'Erro ao salvar o perfil.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Controle de Acesso</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            Configure os perfis e suas permissões de acesso.
          </p>
        </div>

        <CButton color="secondary" size="lg" variant="outline" as={Link} to="/roles">
          Voltar
        </CButton>
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados do Perfil</strong>
        </CCardHeader>

        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}
          {success && <CAlert color="success">{success}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando perfil...</p>
          ) : (
            <CForm onSubmit={handleSubmit}>
              <CRow className="g-3">
                <CCol md={6}>
                  <CFormLabel>Nome técnico</CFormLabel>
                  <CFormInput
                    value={form.name}
                    disabled={isReadOnly}
                    placeholder="Ex: clinic_admin"
                    onChange={(event) =>
                      updateField('name', normalizeSlug(event.target.value))
                    }
                    required
                  />
                </CCol>

                <CCol md={6}>
                  <CFormLabel>Nome de exibição</CFormLabel>
                  <CFormInput
                    value={form.display_name}
                    disabled={isReadOnly}
                    placeholder="Ex: Administrador da Clínica"
                    onChange={(event) =>
                      updateField('display_name', event.target.value)
                    }
                    required
                  />
                </CCol>

                <CCol md={12}>
                  <CFormLabel>Descrição</CFormLabel>
                  <CFormTextarea
                    value={form.description}
                    disabled={isReadOnly}
                    rows={3}
                    placeholder="Descrição opcional do perfil"
                    onChange={(event) =>
                      updateField('description', event.target.value)
                    }
                  />
                </CCol>

                <hr className="my-4" />

                <CCol xs={12}>
                  <h2 className="h5 mb-3">Permissões do Perfil</h2>

                  <CRow className="g-3">
                    {Object.entries(groupedPermissions).map(
                      ([moduleName, modulePermissions]) => (
                        <CCol md={6} key={moduleName}>
                          <CCard className="h-100 border">
                            <CCardHeader className="fw-semibold">
                              {moduleLabels[moduleName] || moduleName}
                            </CCardHeader>

                            <CCardBody className="d-grid gap-2">
                              {modulePermissions.map((permission) => (
                                <div key={permission.id}>
                                  <CFormCheck
                                    id={`permission-${permission.id}`}
                                    label={permission.display_name || permission.name}
                                    checked={selectedPermissionIds.includes(
                                      Number(permission.id),
                                    )}
                                    disabled={isReadOnly}
                                    onChange={() => togglePermission(permission.id)}
                                  />

                                  {permission.description && (
                                    <small className="text-body-secondary d-block ms-4">
                                      {permission.description}
                                    </small>
                                  )}
                                </div>
                              ))}
                            </CCardBody>
                          </CCard>
                        </CCol>
                      ),
                    )}
                  </CRow>
                </CCol>
              </CRow>

              {!isReadOnly && (
                <CButtonGroup className="mt-4">
                  <CButton color="primary" type="submit" disabled={isSaving}>
                    {isSaving ? 'Salvando...' : 'Salvar'}
                  </CButton>

                  <CButton color="secondary" variant="outline" as={Link} to="/roles">
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

export default RoleForm