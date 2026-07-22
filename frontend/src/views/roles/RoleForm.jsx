/**
 * Formulário do módulo de Roles.
 *
 * Usado para:
 * - editar perfil;
 * - vincular permissões ao perfil usando checkboxes.
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
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormTextarea,
  CRow,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'

import { roleService } from 'src/services/roleService'
import { permissionService } from 'src/services/permissionService'
import { rolePermissionService } from 'src/services/rolePermissionService'

import { moduleLabels } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'

const emptyRole = {
  name: '',
  display_name: '',
  description: '',
}

const RoleForm = () => {
  const { id } = useParams()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyRole)
  const [permissions, setPermissions] = useState([])
  const [selectedPermissionIds, setSelectedPermissionIds] = useState([])
  const [isSaving, setIsSaving] = useState(false)

  // O admin_master recebe bypass total na autorização do backend
  // (require_admin/hasPermission) — desmarcar permissões dele aqui
  // altera o banco, mas não reduz o acesso efetivo. Deixar essa matriz
  // editável sugeria uma consequência que não existe de verdade.
  const isAdminMasterRole = form.name === 'admin_master'
  const isPermissionMatrixReadOnly = isAdminMasterRole

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

        const roleData = await roleService.getById(id)
        const linkedPermissions = await rolePermissionService.listByRole(id)

        setForm({
          name: roleData.name ?? '',
          display_name: roleData.display_name ?? '',
          description: roleData.description ?? '',
        })

        setSelectedPermissionIds(linkedPermissions.map((item) => Number(item.permission_id)))
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados do perfil.'))
      } finally {
        stopLoading()
      }
    }

    void loadPageData()
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
   * Monta o payload editável enviado para a API de roles.
   * O nome técnico pertence ao catálogo fechado e não é enviado.
   */
  const buildPayload = () => ({
    display_name: form.display_name.trim(),
    description: form.description.trim() || null,
  })

  const validateForm = () => {
    if (!form.display_name.trim()) return 'Informe o nome de exibição do perfil.'

    return ''
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

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
      await roleService.update(id, buildPayload())
      await rolePermissionService.syncRolePermissions(id, selectedPermissionIds)

      showSuccess(
        'Perfil atualizado com sucesso. Usuários conectados terão os acessos sincronizados ao retornar à aba ou em até 60 segundos.',
      )
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
          <h1 className="h3 mb-0 clinicai-page-title">Editar Perfil</h1>
          <p className="text-body-secondary mb-0">
            Configure os perfis oficiais e suas permissões de acesso.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton
            color="secondary"
            size="lg"
            variant="outline"
            className="clinicai-soft-action"
            as={Link}
            to="/roles"
          >
            Voltar
          </CButton>
        </div>
      </div>

      <div className="alert alert-info">
        Esta tela permite alterar os dados e as permissões do perfil. Revise as informações antes de
        selecionar “Salvar”.
      </div>

      <CCard className="clinicai-card mb-4">
        <CCardHeader className="clinicai-card-header">
          <strong>Dados do Perfil</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={6}>
                <CFormLabel>Perfil</CFormLabel>
                <CFormInput value={form.name} disabled />
                <div className="form-text">
                  Nome técnico definido pelo catálogo oficial do sistema.
                </div>
              </CCol>

              <CCol md={6}>
                <CFormLabel>Nome de exibição</CFormLabel>
                <CFormInput
                  value={form.display_name}
                  placeholder="Ex: Administrador Master"
                  onChange={(event) => updateField('display_name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={12}>
                <CFormLabel>Descrição</CFormLabel>
                <CFormTextarea
                  value={form.description}
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
                    <b>Acesso administrativo amplo:</b> o Administrador Master gerencia os recursos
                    administrativos do sistema. A matriz é somente leitura, mas esse perfil não pode
                    executar ações clínicas nem acessar detalhes, imagens ou resultados médicos dos
                    exames.
                  </div>
                )}

                <CRow className="g-3">
                  {Object.entries(groupedPermissions).map(([moduleName, modulePermissions]) => (
                    <CCol md={6} key={moduleName}>
                      <CCard className="clinicai-card h-100 border">
                        <CCardHeader className="clinicai-card-header fw-semibold">
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

            <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
              <CButton color="primary" type="submit" disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Salvar'}
              </CButton>

              <CButton className="clinicai-modal-cancel-action" variant="outline" as={Link} to="/roles">
                Cancelar
              </CButton>
            </div>
          </CForm>
        </CCardBody>
      </CCard>
    </>
  )
}

export default RoleForm
