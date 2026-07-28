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
  cilPrint,
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
  editColor = 'primary',
  editIcon = cilPencil,
  uploadTo,
  viewTo,
  viewTitle = 'Visualizar',
  viewColor = 'secondary',
  viewIcon = cilUser,
  viewIconClassName,
  isInactive = false,

  onUpload,
  onDownload,
  onPrint,
  onCancel,
  onRestore,
  onInactivate,
  onActivate,

  canView = false,
  canEdit = false,
  canUpload = false,
  canDownload = false,
  downloadTitle = 'Download',
  canPrint = false,
  printTitle = 'Imprimir',
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
  const showPrint = Boolean(onPrint && canPrint)
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
            color={viewColor}
            className="clinicai-action-button rounded-pill"
            as={Link}
            to={viewTo}
            title={viewTitle}
            aria-label={viewTitle}
          >
            <CIcon icon={viewIcon} className={viewIconClassName} />
          </CButton>
        )}

        {showEdit && (
          <CButton color={editColor} className="clinicai-action-button rounded-pill" as={Link} to={editTo} title="Editar">
            <CIcon
              icon={editIcon}
              style={
                editColor === 'info'
                  ? {
                      '--ci-primary-color': '#ffffff',
                      '--ci-secondary-color': '#ffffff',
                      color: '#ffffff',
                      fill: '#ffffff',
                    }
                  : undefined
              }
            />
          </CButton>
        )}

        {showUpload && !uploadTo && (
          <CButton
            color="info"
            className="clinicai-action-button rounded-pill"
            type="button"
            title="Upload"
            onClick={onUpload}
          >
            <CIcon icon={cilCloudUpload} />
          </CButton>
        )}

        {showDownload && (
          <CButton
            color="primary"
            className="clinicai-action-button rounded-pill"
            type="button"
            title={downloadTitle}
            onClick={onDownload}
          >
            <CIcon icon={cilCloudDownload} />
          </CButton>
        )}

        {showPrint && (
          <CButton
            color="secondary"
            className="clinicai-action-button rounded-pill"
            type="button"
            onClick={onPrint}
            title={printTitle}
            aria-label={printTitle}
          >
            <CIcon icon={cilPrint} />
          </CButton>
        )}

        {showInactivate && (
          <CButton
            color="warning"
            className="clinicai-action-button rounded-pill"
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
            className="clinicai-action-button rounded-pill"
            type="button"
            title="Ativar"
            onClick={() => setConfirmVisible(true)}
          >
            <CIcon icon={cilReload} />
          </CButton>
        )}

        {showCancel && (
          <CButton
            color="secondary"
            className="clinicai-action-button rounded-pill"
            type="button"
            title="Cancelar exame"
            aria-label="Cancelar exame"
            onClick={() => openExamConfirm('cancel')}
          >
            <CIcon icon={cilXCircle} />
          </CButton>
        )}

        {showRestore && (
          <CButton
            color="info"
            className="clinicai-action-button rounded-pill"
            type="button"
            title="Restaurar exame"
            aria-label="Restaurar exame"
            onClick={() => openExamConfirm('restore')}
          >
            <CIcon icon={cilReload} className="text-white" />
          </CButton>
        )}
      </CButtonGroup>

      {(showInactivate || showActivate) && (
        <CModal className="clinicai-card" visible={confirmVisible} onClose={handleCloseModal}>
          <CModalHeader className="clinicai-card-header">
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
              className="clinicai-modal-cancel-action"
              onClick={handleCloseModal}
              disabled={isSubmitting}
            >
              Cancelar
            </CButton>

            <CButton
              color="primary"
              className="clinicai-modal-primary-action"
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
              {examActionType === 'cancel' ? 'Cancelar Exame' : 'Restaurar Exame'}
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
                Você deseja restaurar <strong>{itemLabel}</strong>? O exame voltará para o fluxo de
                atendimento.
              </>
            )}
          </CModalBody>

          <CModalFooter>
            <CButton
              color="secondary"
              variant="outline"
              className="clinicai-modal-cancel-action"
              onClick={handleCloseExamModal}
              disabled={isSubmitting}
            >
              Cancelar
            </CButton>

            <CButton
              color="primary"
              className="clinicai-modal-primary-action"
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
                'Restaurar'
              )}
            </CButton>
          </CModalFooter>
        </CModal>
      )}
    </>
  )
}

export default AppActionButtons
