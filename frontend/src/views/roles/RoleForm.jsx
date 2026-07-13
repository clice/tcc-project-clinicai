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
  CFormSelect,
  CFormTextarea,
  CRow,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { roleService } from 'src/services/roleService'
import { permissionService } from 'src/services/permissionService'
import { rolePermissionService } from 'src/services/rolePermissionService'

import { moduleLabels, roleLabels, roleOptions } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'

const emptyRole = {
  name: '',
  display_name: '',
  description: '',
}

const RoleForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()
  const { refreshUser } = useAuth()

  const [form, setForm] = useState(emptyRole)
  const [permissions, setPermissions] = useState([])
  const [selectedPermissionIds, setSelectedPermissionIds] = useState([])
  const [isSaving, setIsSaving] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  // O admin_master recebe bypass total na autorização do backend
  // (require_admin/hasPermission) — desmarcar permissões dele aqui
  // altera o banco, mas não reduz o acesso efetivo. Deixar essa matriz
  // editável sugeria uma consequência que não existe de verdade.
  const isAdminMasterRole = form.name === 'admin_master'
  const isPermissionMatrixReadOnly = isReadOnly || isAdminMasterRole

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
        startLoading()
        showError('')

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

          setSelectedPermissionIds(linkedPermissions.map((item) => Number(item.permission_id)))
        }
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados do perfil.'))
      } finally {
        stopLoading()
      }
    }

    void loadPageData()
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
   * 'name' só é enviado na criação — na edição é imutável (o backend
   * nem aceita mais esse campo em RoleUpdate).
   */
  const buildPayload = () => {
    if (isEditMode) {
      return {
        display_name: form.display_name.trim(),
        description: form.description.trim() || null,
      }
    }

    return {
      name: form.name,
      display_name: form.display_name.trim(),
      description: form.description.trim() || null,
    }
  }

  const validateForm = () => {
    if (!form.name) return 'Selecione o perfil.'
    if (!form.display_name.trim()) return 'Informe o nome de exibição do perfil.'

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    setIsSaving(true)
    showError('')
    showSuccess('')

    const validationError = validateForm()

    if (validationError) {
      showError(validationError)
      setIsSaving(false)
      return
    }

    try {
      if (isCreateMode) {
        const createdRole = await roleService.create(buildPayload())

        await rolePermissionService.syncRolePermissions(createdRole.id, selectedPermissionIds)

        navigate(`/roles/${createdRole.id}`)
        return
      }

      if (isEditMode) {
        await roleService.update(id, buildPayload())
        await rolePermissionService.syncRolePermissions(id, selectedPermissionIds)

        // Se o usuário logado pertencer à role que acabou de ser editada,
        // a lista de permissões dele (recebida uma única vez em
        // /auth/me, no login) fica desatualizada até relogar — botões e
        // menus baseados em permissão continuariam visíveis mesmo que o
        // backend já negasse a ação com 403. Chamar refreshUser aqui
        // resolve isso para o próprio editor, sem esperar um novo login.
        await refreshUser()

        showSuccess('Perfil atualizado com sucesso.')
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar o perfil.'))
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
            Configure os perfis oficiais e suas permissões de acesso.
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
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={6}>
                <CFormLabel>Perfil</CFormLabel>
                <CFormSelect
                  value={form.name}
                  disabled={isReadOnly || isEditMode}
                  onChange={(event) => updateField('name', event.target.value)}
                  required
                >
                  <option value="">Selecione...</option>
                  {roleOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </CFormSelect>
                {isEditMode && (
                  <div className="form-text">
                    O perfil não pode ser alterado após a criação.
                  </div>
                )}
              </CCol>

              <CCol md={6}>
                <CFormLabel>Nome de exibição</CFormLabel>
                <CFormInput
                  value={form.display_name}
                  disabled={isReadOnly}
                  placeholder="Ex: Administrador Master"
                  onChange={(event) => updateField('display_name', event.target.value)}
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
                  onChange={(event) => updateField('description', event.target.value)}
                />
              </CCol>

              <hr className="my-4" />

              <CCol xs={12}>
                <h2 className="h5 mb-3">Permissões do Perfil</h2>

                {isAdminMasterRole && (
                  <div className="alert alert-info small mb-3">
                    Acesso total fixo — o Administrador Master tem acesso irrestrito ao sistema
                    por padrão. Esta matriz é somente leitura porque desmarcar itens aqui não
                    reduz o acesso efetivo desse perfil.
                  </div>
                )}

                <CRow className="g-3">
                  {Object.entries(groupedPermissions).map(([moduleName, modulePermissions]) => (
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
                                checked={selectedPermissionIds.includes(Number(permission.id))}
                                disabled={isPermissionMatrixReadOnly}
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
                  ))}
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
        </CCardBody>
      </CCard>
    </>
  )
}

export default RoleForm