import React from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CSpinner,
} from '@coreui/react'

import {
  aiStatusColors,
  aiStatusLabels,
  predictionLabels,
} from 'src/utils/constants'

const modelDisplayNames = {
  ensemble_stacking:
    'ClinicAI Gastrointestinal — Ensemble Stacking',
  clinicai_stacking:
    'ClinicAI Gastrointestinal — Ensemble Stacking',
}

const getModelDisplayName = (modelName) =>
  modelDisplayNames[modelName] || modelName || '-'

const formatConfidence = (value) => {
  if (value === undefined || value === null) {
    return '-'
  }

  return `${Math.round(value * 100)}%`
}

const imageAreaStyle = {
  height: '360px',
  objectFit: 'contain',
}

const loadingAreaStyle = {
  minHeight: '360px',
}

const contributionScaleStyle = {
  height: '14px',
  background:
    'linear-gradient(90deg, #000080 0%, #0066ff 25%, #00ffff 45%, #ffff00 70%, #ff0000 100%)',
}

const ExamAiResultCard = ({
  aiStatus,
  aiAnalysis,
  canViewAiAnalysis,
  canDownloadExamFile,
  originalImageUrl,
  originalImageError,
  isOriginalImageLoading,
  isOriginalDownloading,
  onOriginalDownload,
  gradcamUrl,
  gradcamError,
  isGradcamLoading,
  isGradcamDownloading,
  onGradcamDownload,
}) => {
  const hasGradcam = Boolean(
    aiAnalysis?.gradcam_available,
  )

  const statusLabel =
    aiStatusLabels[aiStatus] ||
    aiStatus ||
    '-'

  return (
    <CCard>
      <CCardHeader>
        <strong>Resultado da IA</strong>
      </CCardHeader>

      <CCardBody>
        {canViewAiAnalysis ? (
          <>
            <CAlert
              color="info"
              className="small"
            >
              <div className="mb-2">
                <strong>Uso do resultado:</strong>{' '}
                Este resultado é gerado automaticamente para
                apoio à análise. Ele pode conter erros e não
                substitui a avaliação do profissional
                responsável.
              </div>

              <div>
                <strong>Sobre o mapa atual:</strong>{' '}
                A classificação e a confiança são produzidas pelo
                Ensemble Stacking. O mapa Grad-CAM exibido é
                gerado separadamente a partir da ResNet-50 e não
                explica sozinho a decisão completa do ensemble.
                As cores indicam contribuição relativa, não
                representam risco, gravidade ou probabilidade
                clínica.
              </div>
            </CAlert>

            <CRow className="g-3">
              <CCol md={4}>
                <div className="text-body-secondary small">
                  Status da análise
                </div>

                <CBadge
                  color={
                    aiStatusColors[aiStatus] ||
                    'secondary'
                  }
                >
                  {statusLabel}
                </CBadge>
              </CCol>

              <CCol md={4}>
                <div className="text-body-secondary small">
                  Predição
                </div>

                {aiAnalysis ? (
                  <CBadge
                    color={
                      aiAnalysis.prediction_class === 1
                        ? 'danger'
                        : 'success'
                    }
                  >
                    {predictionLabels[
                      aiAnalysis.prediction_label
                    ] ||
                      aiAnalysis.prediction_label ||
                      '-'}
                  </CBadge>
                ) : (
                  <div>-</div>
                )}
              </CCol>

              <CCol md={4}>
                <div className="text-body-secondary small">
                  Confiança
                </div>

                <strong>
                  {formatConfidence(
                    aiAnalysis?.confidence,
                  )}
                </strong>
              </CCol>
            </CRow>

            <CRow className="g-3 mt-1">
              <CCol md={6}>
                <div className="text-body-secondary small">
                  Modelo utilizado
                </div>

                <div>
                  {getModelDisplayName(
                    aiAnalysis?.model_name,
                  )}
                </div>
              </CCol>

              <CCol md={3}>
                <div className="text-body-secondary small">
                  Versão
                </div>

                <div>
                  {aiAnalysis?.model_version || '-'}
                </div>
              </CCol>

              <CCol md={3}>
                <div className="text-body-secondary small">
                  Tempo de processamento
                </div>

                <div>
                  {aiAnalysis?.processing_time_ms !== null &&
                  aiAnalysis?.processing_time_ms !== undefined
                    ? `${aiAnalysis.processing_time_ms} ms`
                    : '-'}
                </div>
              </CCol>
            </CRow>

            {aiStatus === 'processing' &&
              !aiAnalysis && (
                <CAlert
                  color="info"
                  className="d-flex align-items-center gap-2 mt-4 mb-0"
                >
                  <CSpinner size="sm" />

                  <span>
                    A análise está sendo executada. Uma segunda
                    execução permanece bloqueada.
                  </span>
                </CAlert>
              )}

            {aiStatus === 'failed' &&
              !aiAnalysis && (
                <CAlert
                  color="danger"
                  className="mt-4 mb-0"
                >
                  A análise falhou. Restaure o exame antes de
                  realizar uma nova tentativa.
                </CAlert>
              )}

            {aiStatus !== 'processing' &&
              aiStatus !== 'failed' &&
              !aiAnalysis && (
                <CAlert
                  color="secondary"
                  className="mt-4 mb-0"
                >
                  Este exame ainda não possui análise de IA
                  vinculada.
                </CAlert>
              )}

            {aiAnalysis?.ai_notes?.trim() && (
              <div className="mt-4">
                <div className="text-body-secondary small">
                  Observações técnicas da IA
                </div>

                <div>{aiAnalysis.ai_notes}</div>
              </div>
            )}
          </>
        ) : (
          <CAlert
            color="secondary"
            className="mb-0"
          >
            Você não possui permissão para visualizar o resultado
            automatizado da análise.
          </CAlert>
        )}

        <hr className="my-4" />

        {canViewAiAnalysis && hasGradcam && (
          <div className="mb-4">
            <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
              <div className="small fw-semibold">
                Intensidade de contribuição relativa
              </div>

              <div className="small text-body-secondary">
                Legenda do mapa Grad-CAM
              </div>
            </div>

            <div
              className="rounded border"
              style={contributionScaleStyle}
              role="img"
              aria-label="Escala de azul para vermelho representando menor e maior contribuição relativa"
            />

            <div className="d-flex justify-content-between gap-3 small text-body-secondary mt-1">
              <span>Menor contribuição</span>
              <span>Maior contribuição</span>
            </div>
          </div>
        )}

        <div className="position-relative">
          <CRow className="g-4 align-items-stretch">
            <CCol lg={6}>
              <section
                aria-labelledby="original-image-title"
                className="h-100 d-flex flex-column"
              >
                <h2
                  id="original-image-title"
                  className="h6 mb-3"
                >
                  Imagem original
                </h2>

                {!canDownloadExamFile ? (
                  <CAlert
                    color="secondary"
                    className="mb-0"
                  >
                    Você não possui permissão para acessar a
                    imagem original.
                  </CAlert>
                ) : isOriginalImageLoading ? (
                  <div
                    className="d-flex align-items-center justify-content-center gap-2 text-body-secondary"
                    style={loadingAreaStyle}
                  >
                    <CSpinner size="sm" />

                    <span>
                      Carregando imagem original...
                    </span>
                  </div>
                ) : originalImageUrl ? (
                  <>
                    <a
                      href={originalImageUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="d-block mb-3 text-center"
                    >
                      <img
                        src={originalImageUrl}
                        alt="Imagem original do exame"
                        className="w-100 rounded border bg-body-tertiary"
                        style={imageAreaStyle}
                      />
                    </a>

                    <div className="d-grid gap-2 mt-auto">
                      <CButton
                        color="secondary"
                        variant="outline"
                        href={originalImageUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Abrir imagem original em tamanho maior
                      </CButton>

                      <CButton
                        color="primary"
                        onClick={onOriginalDownload}
                        disabled={isOriginalDownloading}
                      >
                        {isOriginalDownloading ? (
                          <>
                            <CSpinner
                              size="sm"
                              className="me-2"
                            />
                            Baixando...
                          </>
                        ) : (
                          'Baixar imagem original'
                        )}
                      </CButton>
                    </div>
                  </>
                ) : (
                  <CAlert
                    color="warning"
                    className="mb-0"
                  >
                    {originalImageError ||
                      'Imagem original não disponível.'}
                  </CAlert>
                )}
              </section>
            </CCol>

            <CCol lg={6}>
              <hr className="d-lg-none my-0 mb-4" />

              <section
                aria-labelledby="gradcam-image-title"
                className="h-100 d-flex flex-column"
              >
                <h2
                  id="gradcam-image-title"
                  className="h6 mb-3"
                >
                  Mapa Grad-CAM
                </h2>

                {!canViewAiAnalysis ? (
                  <CAlert
                    color="secondary"
                    className="mb-0"
                  >
                    Você não possui permissão para acessar o mapa
                    Grad-CAM.
                  </CAlert>
                ) : !hasGradcam ? (
                  <CAlert
                    color="secondary"
                    className="mb-0"
                  >
                    Este exame não possui mapa Grad-CAM
                    disponível.
                  </CAlert>
                ) : isGradcamLoading ? (
                  <div
                    className="d-flex align-items-center justify-content-center gap-2 text-body-secondary"
                    style={loadingAreaStyle}
                  >
                    <CSpinner size="sm" />

                    <span>
                      Carregando mapa Grad-CAM...
                    </span>
                  </div>
                ) : gradcamUrl ? (
                  <>
                    <a
                      href={gradcamUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="d-block mb-3 text-center"
                    >
                      <img
                        src={gradcamUrl}
                        alt="Mapa Grad-CAM destacando regiões que contribuíram para a predição"
                        className="w-100 rounded border bg-body-tertiary"
                        style={imageAreaStyle}
                      />
                    </a>

                    <div className="d-grid gap-2 mt-auto">
                      <CButton
                        color="secondary"
                        variant="outline"
                        href={gradcamUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Abrir mapa em tamanho maior
                      </CButton>

                      <CButton
                        color="primary"
                        onClick={onGradcamDownload}
                        disabled={isGradcamDownloading}
                      >
                        {isGradcamDownloading ? (
                          <>
                            <CSpinner
                              size="sm"
                              className="me-2"
                            />
                            Baixando...
                          </>
                        ) : (
                          'Baixar mapa Grad-CAM'
                        )}
                      </CButton>
                    </div>
                  </>
                ) : (
                  <CAlert
                    color="warning"
                    className="mb-0"
                  >
                    {gradcamError ||
                      'Mapa Grad-CAM não disponível.'}
                  </CAlert>
                )}
              </section>
            </CCol>
          </CRow>

          <div
            className="d-none d-lg-block position-absolute top-0 bottom-0 start-50 border-start"
            aria-hidden="true"
          />
        </div>
      </CCardBody>
    </CCard>
  )
}

export default ExamAiResultCard
