import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CButton,
  CButtonGroup,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import {
  cilCloudUpload,
  cilFolderOpen,
  cilUser,
  cilPencil,
  cilReload,
} from '@coreui/icons'

/**
 * Botões genéricos de ação para tabelas.
 *
 * Usado para:
 * - visualizar;
 * - editar;
 * - upload;
 * - inativar;
 * - ativar.
 */
const AppActionButtons = ({
  itemLabel,
  editTo,
  uploadTo,
  viewTo,
  isInactive = false,
  onInactivate,
  onActivate,
  canView = true,
  canEdit = true,
  canUpload = true,
  canInactivate = true,
  canActivate = true,
}) => {
  const [confirmVisible, setConfirmVisible] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const showView = Boolean(viewTo && canView)
  const showEdit = Boolean(editTo && !isInactive && canEdit)
  const showUpload = Boolean(uploadTo && !isInactive && canUpload)

  const showInactivate = Boolean(!isInactive && onInactivate && canInactivate)
  const showActivate = Boolean(isInactive && onActivate && canActivate)

  const actionType = showInactivate ? 'inactivate' : showActivate ? 'activate' : null

  const handleCloseModal = () => {
    if (!isSubmitting) {
      setConfirmVisible(false)
    }
  }

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true)

      if (actionType === 'inactivate') {
        await onInactivate()
      }

      if (actionType === 'activate') {
        await onActivate()
      }

      setConfirmVisible(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <CButtonGroup className="d-flex gap-2" size="sm" role="group">
        {showView && (
          <CButton color="secondary" className="rounded-pill" as={Link} to={viewTo} title="Visualizar">
            <CIcon icon={cilUser} />
          </CButton>
        )}

        {showEdit && (
          <CButton color="primary" className="rounded-pill" as={Link} to={editTo} title="Editar">
            <CIcon icon={cilPencil} />
          </CButton>
        )}

        {showUpload && (
          <CButton color="info" className="rounded-pill" as={Link} to={uploadTo} title="Upload">
            <CIcon icon={cilCloudUpload} />
          </CButton>
        )}

        {showInactivate && (
          <CButton color="warning" className="rounded-pill" type="button" title="Inativar" onClick={() => setConfirmVisible(true)}>
            <CIcon icon={cilFolderOpen} />
          </CButton>
        )}

        {showActivate && (
          <CButton color="success" className="rounded-pill" type="button" title="Ativar" onClick={() => setConfirmVisible(true)}>
            <CIcon icon={cilReload} />
          </CButton>
        )}
      </CButtonGroup>

      {(showInactivate || showActivate) && (
        <CModal visible={confirmVisible} onClose={handleCloseModal}>
          <CModalHeader>
            <CModalTitle>
              {actionType === 'inactivate' ? 'Inativar Registro' : 'Ativar Registro'}
            </CModalTitle>
          </CModalHeader>

          <CModalBody>
            {actionType === 'inactivate' ? (
              <>
                Você deseja inativar <strong>{itemLabel}</strong>? O registro será movido para a aba de inativos.
              </>
            ) : (
              <>
                Você deseja ativar <strong>{itemLabel}</strong>? O registro voltará para a aba de ativos.
              </>
            )}
          </CModalBody>

          <CModalFooter>
            <CButton color="secondary" variant="outline" onClick={handleCloseModal} disabled={isSubmitting}>
              Cancelar
            </CButton>

            <CButton color={actionType === 'inactivate' ? 'warning' : 'success'} onClick={handleConfirm} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <CSpinner size="sm" className="me-2" />
                  Processando...
                </>
              ) : actionType === 'inactivate' ? (
                'Inativar'
              ) : (
                'Ativar'
              )}
            </CButton>
          </CModalFooter>
        </CModal>
      )}
    </>
  )
}

export default AppActionButtons