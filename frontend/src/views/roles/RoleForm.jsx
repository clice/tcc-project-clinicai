/**
 * Formulário do módulo de Roles.
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

import { roleService } from 'src/services/roleService'
import { permissionService } from 'src/services/permissionService'
import { rolePermissionService } from 'src/services/rolePermissionService'

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
  ai_analysis: 'Análises IA',
  roles: 'Perfis',
  permissions: 'Permissões',
  statuses: 'Status',
  audit_logs: 'Logs de Auditoria',
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

  /**
   * Agrupa permissões pelo módulo.
   *
   * Isso deixa a tela mais organizada visualmente.
   */
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
    const loadPageData = async () => {
      try {
        setIsLoading(true)
        setError('')

        const permissionsData = await permissionService.list()
        setPermissions(Array.isArray(permissionsData) ? permissionsData : [])

        if (!isCreateMode) {
          const roleData = await roleService.getById(id)
          const linkedPermissions = await rolePermissionService.listByRole(id)

          setForm({
            name: roleData.name ?? '',
            display_name: roleData.display_name ?? '',
            description: roleData.description ?? '',
          })

          /**
           * Guarda apenas os IDs das permissões já vinculadas ao perfil.
           */
          setSelectedPermissionIds(
            linkedPermissions.map((item) => Number(item.permission_id)),
          )
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Erro ao carregar dados do perfil.')
      } finally {
        setIsLoading(false)
      }
    }

    loadPageData()
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

  const normalizeName = (value) => {
    return value
      .trim()
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  }

  /**
   * Marca ou desmarca uma permissão.
   *
   * A gravação no backend acontece apenas ao clicar em Salvar.
   */
  const togglePermission = (permissionId) => {
    setSelectedPermissionIds((current) => {
      const numericId = Number(permissionId)

      if (current.includes(numericId)) {
        return current.filter((id) => id !== numericId)
      }

      return [...current, numericId]
    })
  }

  /**
   * Monta o payload enviado para a API de roles.
   */
  const buildPayload = () => ({
    name: normalizeName(form.name),
    display_name: form.display_name.trim(),
    description: form.description.trim() || null,
  })

  const validateForm = () => {
    if (!form.name.trim()) return 'Informe o nome técnico do perfil.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição do perfil.'

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
      if (isCreateMode) {
        const createdRole = await roleService.create(buildPayload())

        /**
         * Após criar a role, vinculamos as permissões selecionadas.
         */
        await rolePermissionService.syncRolePermissions(
          createdRole.id,
          selectedPermissionIds,
        )

        navigate(`/roles/${createdRole.id}`)
        return
      }

      if (isEditMode) {
        await roleService.update(id, buildPayload())

        /**
         * Sincroniza a tabela role_permissions:
         * - adiciona permissões marcadas novas;
         * - remove permissões que foram desmarcadas;
         * - mantém as que não mudaram.
         */
        await rolePermissionService.syncRolePermissions(id, selectedPermissionIds)

        setSuccess('Perfil atualizado com sucesso.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao salvar o perfil.')
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

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/roles">
            Voltar
          </CButton>
        </div>
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