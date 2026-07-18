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
  cilCloudDownload,
  cilCloudUpload,
  cilFolderOpen,
  cilUser,
  cilPencil,
  cilReload,
  cilXCircle,
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

  onUpload,
  onDownload,
  onCancel,
  onRestore,
  onInactivate,
  onActivate,

  canView = false,
  canEdit = false,
  canUpload = false,
  canDownload = false,
  downloadTitle = 'Download',
  canCancel = false,
  canRestore = false,
  canInactivate = false,
  canActivate = false,
}) => {
  const [confirmVisible, setConfirmVisible] = useState(false)
  const [examConfirmVisible, setExamConfirmVisible] = useState(false)
  const [examActionType, setExamActionType] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const showView = Boolean(viewTo && canView)
  const showEdit = Boolean(editTo && !isInactive && canEdit)
  const showUpload = Boolean((uploadTo || onUpload) && !isInactive && canUpload)
  const showDownload = Boolean(onDownload && canDownload)
  const showCancel = Boolean(onCancel && canCancel)
  const showRestore = Boolean(onRestore && canRestore)

  const showInactivate = Boolean(!isInactive && onInactivate && canInactivate)
  const showActivate = Boolean(isInactive && onActivate && canActivate)

  const actionType = showInactivate ? 'inactivate' : showActivate ? 'activate' : null

  const handleCloseModal = () => {
    if (!isSubmitting) {
      setConfirmVisible(false)
    }
  }

  const handleCloseExamModal = () => {
    if (!isSubmitting) {
      setExamConfirmVisible(false)
      setExamActionType(null)
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

  const handleExamConfirm = async () => {
    try {
      setIsSubmitting(true)

      if (examActionType === 'cancel') {
        await onCancel()
      }

      if (examActionType === 'restore') {
        await onRestore()
      }

      setExamConfirmVisible(false)
      setExamActionType(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  const openExamConfirm = (type) => {
    setExamActionType(type)
    setExamConfirmVisible(true)
  }

  return (
    <>
      <CButtonGroup className="d-flex gap-2" size="sm" role="group">
        {showView && (
          <CButton
            color="secondary"
            className="rounded-pill"
            as={Link}
            to={viewTo}
            title="Visualizar"
          >
            <CIcon icon={cilUser} />
          </CButton>
        )}

        {showEdit && (
          <CButton color="primary" className="rounded-pill" as={Link} to={editTo} title="Editar">
            <CIcon icon={cilPencil} />
          </CButton>
        )}

        {showUpload && !uploadTo && (
          <CButton
            color="info"
            className="rounded-pill text-white"
            type="button"
            title="Upload"
            onClick={onUpload}
          >
            <CIcon icon={cilCloudUpload} />
          </CButton>
        )}

        {showDownload && (
          <CButton
            color="info"
            className="rounded-pill text-white"
            type="button"
            title={downloadTitle}
            onClick={onDownload}
          >
            <CIcon icon={cilCloudDownload} />
          </CButton>
        )}

        {showInactivate && (
          <CButton
            color="warning"
            className="rounded-pill"
            type="button"
            title="Inativar"
            onClick={() => setConfirmVisible(true)}
          >
            <CIcon icon={cilFolderOpen} />
          </CButton>
        )}

        {showActivate && (
          <CButton
            color="success"
            className="rounded-pill"
            type="button"
            title="Ativar"
            onClick={() => setConfirmVisible(true)}
          >
            <CIcon icon={cilReload} />
          </CButton>
        )}

        {showCancel && (
          <CButton
            color="danger"
            className="rounded-pill text-white"
            type="button"
            title="Cancelar exame"
            onClick={() => openExamConfirm('cancel')}
          >
            <CIcon icon={cilXCircle} />
          </CButton>
        )}

        {showRestore && (
          <CButton
            color="success"
            className="rounded-pill"
            type="button"
            title="Retomar exame"
            onClick={() => openExamConfirm('restore')}
          >
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
                Você deseja inativar <strong>{itemLabel}</strong>? O registro será movido para a aba
                de inativos.
              </>
            ) : (
              <>
                Você deseja ativar <strong>{itemLabel}</strong>? O registro voltará para a aba de
                ativos.
              </>
            )}
          </CModalBody>

          <CModalFooter>
            <CButton
              color="secondary"
              variant="outline"
              onClick={handleCloseModal}
              disabled={isSubmitting}
            >
              Cancelar
            </CButton>

            <CButton
              color={actionType === 'inactivate' ? 'warning' : 'success'}
              onClick={handleConfirm}
              disabled={isSubmitting}
            >
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

      {(showCancel || showRestore) && (
        <CModal visible={examConfirmVisible} onClose={handleCloseExamModal}>
          <CModalHeader>
            <CModalTitle>
              {examActionType === 'cancel' ? 'Cancelar Exame' : 'Retomar Exame'}
            </CModalTitle>
          </CModalHeader>

          <CModalBody>
            {examActionType === 'cancel' ? (
              <>
                Você deseja cancelar <strong>{itemLabel}</strong>? O exame será movido para
                cancelados.
              </>
            ) : (
              <>
                Você deseja retomar <strong>{itemLabel}</strong>? O exame voltará para o fluxo de
                atendimento.
              </>
            )}
          </CModalBody>

          <CModalFooter>
            <CButton
              color="secondary"
              variant="outline"
              onClick={handleCloseExamModal}
              disabled={isSubmitting}
            >
              Fechar
            </CButton>

            <CButton
              color={examActionType === 'cancel' ? 'danger' : 'success'}
              onClick={handleExamConfirm}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <CSpinner size="sm" className="me-2" />
                  Processando...
                </>
              ) : examActionType === 'cancel' ? (
                'Cancelar Exame'
              ) : (
                'Retomar'
              )}
            </CButton>
          </CModalFooter>
        </CModal>
      )}
    </>
  )
}

export default AppActionButtons
