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
import CIcon from '@coreui/icons-react'
import {
  cilCloudDownload,
  cilPrint,
} from '@coreui/icons'

import {
  aiStatusColors,
  aiStatusLabels,
  predictionLabels,
} from 'src/utils/constants'

const modelDisplayNames = {
  ensemble_stacking:
    'ClinicAI ES Gastrointestinal',
  clinicai_stacking:
    'ClinicAI ES Gastrointestinal',
}

const getModelDisplayName = (
  modelName,
) =>
  modelDisplayNames[modelName] ||
  modelName ||
  '-'

const formatConfidence = (value) => {
  if (
    value === undefined ||
    value === null
  ) {
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

const ENSEMBLE_ATTRIBUTION_METHOD =
  'weighted_base_gradcam_oriented_by_ensemble_stacking_v1'

const formatAttributionWeight = (
  value,
) => {
  if (
    typeof value !== 'number' ||
    !Number.isFinite(value)
  ) {
    return '-'
  }

  return `${(value * 100).toFixed(1)}%`
}

const ExamAiResultCard = ({
  aiStatus,
  aiAnalysis,
  canViewAiAnalysis,
  canDownloadExamFile,
  canDownloadExamPackage,
  originalImageUrl,
  originalImageError,
  isOriginalImageLoading,
  gradcamUrl,
  gradcamError,
  isGradcamLoading,
  isPackageDownloading,
  onPackageDownload,
  reviewPanel = null,
}) => {
  const hasAttributionMap = Boolean(
    aiAnalysis?.gradcam_available,
  )

  const isEnsembleAttribution =
    aiAnalysis?.attribution_method ===
    ENSEMBLE_ATTRIBUTION_METHOD

  const attributionWeights =
    aiAnalysis?.attribution_branch_weights

  const mapTitle =
    isEnsembleAttribution
      ? 'Mapa de atribuição composto'
      : aiAnalysis
        ? 'Mapa Grad-CAM (ResNet-50)'
        : 'Mapa de atribuição'

  const mapName =
    isEnsembleAttribution
      ? 'mapa de atribuição composto'
      : 'Mapa Grad-CAM legado da ResNet-50'

  const statusLabel =
    aiStatusLabels[aiStatus] ||
    aiStatus ||
    '-'

  return (
    <CCard>
      <CCardHeader>
        <strong>
          Análise Automatizada e Revisão Médica
        </strong>
      </CCardHeader>

      <CCardBody>
        {canViewAiAnalysis &&
          hasAttributionMap && (
            <CRow className="g-3 mb-4 align-items-center">
              <CCol
                lg={
                  canDownloadExamPackage
                    ? 6
                    : 12
                }
              >
                <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
                  <div className="small fw-semibold">
                    Intensidade de atribuição
                    relativa
                  </div>

                  <div className="small text-body-secondary">
                    Escala do mapa de
                    atribuição
                  </div>
                </div>

                <div
                  className="rounded border"
                  style={
                    contributionScaleStyle
                  }
                  role="img"
                  aria-label="Escala de azul para vermelho representando menor e maior intensidade relativa"
                />

                <div className="d-flex justify-content-between gap-3 small text-body-secondary mt-1">
                  <span>
                    Menor intensidade
                  </span>

                  <span>
                    Maior intensidade
                  </span>
                </div>

              </CCol>

              {canDownloadExamPackage && (
                <CCol
                  lg={6}
                  className="ps-lg-5"
                >
                  <div
                    className="d-flex flex-wrap align-items-center justify-content-center justify-content-lg-end gap-3"
                    role="group"
                    aria-label="Ações do exame"
                  >
                    <CButton
                      color="primary"
                      className="d-inline-flex align-items-center justify-content-center text-nowrap px-4"
                      type="button"
                      title="Baixar imagem original e mapa de atribuição"
                      aria-label="Baixar imagem original e mapa de atribuição"
                      onClick={
                        onPackageDownload
                      }
                      disabled={
                        isPackageDownloading
                      }
                    >
                      {isPackageDownloading ? (
                        <>
                          <CSpinner
                            size="sm"
                            className="me-2"
                          />

                          <span>
                            Baixando...
                          </span>
                        </>
                      ) : (
                        <>
                          <CIcon
                            icon={
                              cilCloudDownload
                            }
                            className="me-2"
                          />

                          <span>
                            Baixar
                          </span>
                        </>
                      )}
                    </CButton>

                    {/* <CButton
                      color="secondary"
                      variant="outline"
                      className="d-inline-flex align-items-center justify-content-center text-nowrap px-4"
                      type="button"
                      title="Impressão do exame ainda não disponível"
                      aria-label="Impressão do exame ainda não disponível"
                      disabled
                    >
                      <CIcon
                        icon={cilPrint}
                        className="me-2"
                      />

                      <span>
                        Imprimir
                      </span>
                    </CButton> */}
                  </div>
                </CCol>
              )}
            </CRow>
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
                    Você não possui permissão
                    para acessar a imagem
                    original.
                  </CAlert>
                ) : isOriginalImageLoading ? (
                  <div
                    className="d-flex align-items-center justify-content-center gap-2 text-body-secondary"
                    style={loadingAreaStyle}
                  >
                    <CSpinner size="sm" />

                    <span>
                      Carregando imagem
                      original...
                    </span>
                  </div>
                ) : originalImageUrl ? (
                  <div className="text-center">
                    <img
                      src={originalImageUrl}
                      alt="Imagem original do exame"
                      className="w-100 rounded border bg-body-tertiary"
                      style={imageAreaStyle}
                    />
                  </div>
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
                aria-labelledby="attribution-image-title"
                className="h-100 d-flex flex-column"
              >
                <h2
                  id="attribution-image-title"
                  className="h6 mb-3"
                >
                  {mapTitle}
                </h2>

                {!canViewAiAnalysis ? (
                  <CAlert
                    color="secondary"
                    className="mb-0"
                  >
                    Você não possui permissão
                    para acessar o mapa de
                    atribuição.
                  </CAlert>
                ) : !hasAttributionMap ? (
                  <CAlert
                    color="secondary"
                    className="mb-0"
                  >
                    Este exame não possui{' '}
                    {mapName} disponível.
                  </CAlert>
                ) : isGradcamLoading ? (
                  <div
                    className="d-flex align-items-center justify-content-center gap-2 text-body-secondary"
                    style={loadingAreaStyle}
                  >
                    <CSpinner size="sm" />

                    <span>
                      Carregando {mapName}...
                    </span>
                  </div>
                ) : gradcamUrl ? (
                  <div className="text-center">
                    <img
                      src={gradcamUrl}
                      alt={
                        isEnsembleAttribution
                          ? 'Mapa de atribuição composto com regiões associadas à classe final prevista'
                          : 'Mapa Grad-CAM legado da ResNet-50'
                      }
                      className="w-100 rounded border bg-body-tertiary"
                      style={imageAreaStyle}
                    />
                  </div>
                ) : (
                  <CAlert
                    color="warning"
                    className="mb-0"
                  >
                    {gradcamError ||
                      `${mapTitle} não disponível.`}
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

        <hr className="my-4" />

        <CRow className="g-4 align-items-stretch">
          <CCol
            lg={
              reviewPanel
                ? 6
                : 12
            }
          >
            <section
              aria-labelledby="analysis-data-title"
              className="h-100"
            >
              <h2
                id="analysis-data-title"
                className="h5 mb-3"
              >
                Dados da análise
              </h2>

              {!canViewAiAnalysis ? (
                <CAlert
                  color="secondary"
                  className="mb-0"
                >
                  Você não possui permissão para
                  visualizar o resultado
                  automatizado da análise.
                </CAlert>
              ) : (
                <>
                  <CAlert
                    color="info"
                    className="small"
                  >
                    <div className="mb-2">
                      <strong>
                        Uso do resultado:
                      </strong>{' '}
                      Este resultado é gerado
                      automaticamente para apoio à
                      análise. Ele pode conter erros
                      e não substitui a avaliação do
                      profissional responsável.
                    </div>

                    <div>
                      <strong>
                        Sobre o mapa:
                      </strong>{' '}
                      {isEnsembleAttribution ? (
                        <>
                          A classificação e a
                          confiança são produzidas
                          pelo Ensemble Stacking. O
                          mapa de atribuição composto
                          combina os mapas Grad-CAM
                          da ResNet-50,
                          EfficientNet-B4 e PVTv2-B2,
                          ponderados pelas evidências
                          locais do metaclassificador
                          para a classe final prevista.
                          As cores representam
                          atribuição relativa, e não
                          risco, gravidade,
                          causalidade ou probabilidade
                          clínica.
                        </>
                      ) : (
                        <>
                          Este é um Mapa Grad-CAM
                          legado gerado separadamente
                          pela ResNet-50. Ele não
                          explica sozinho a decisão
                          completa do Ensemble
                          Stacking.
                        </>
                      )}
                    </div>

                    {isEnsembleAttribution &&
                      attributionWeights && (
                        <div className="mt-2">
                          <strong>
                            Pesos locais da
                            composição:
                          </strong>{' '}
                          ResNet-50{' '}
                          {formatAttributionWeight(
                            attributionWeights.resnet50,
                          )}
                          ; EfficientNet-B4{' '}
                          {formatAttributionWeight(
                            attributionWeights.efficientnet_b4,
                          )}
                          ; PVTv2-B2{' '}
                          {formatAttributionWeight(
                            attributionWeights.pvt_v2_b2,
                          )}
                          .
                        </div>
                      )}
                  </CAlert>

                  <CRow className="g-3">
                    <CCol md={4}>
                      <div className="text-body-secondary small">
                        Status da análise
                      </div>

                      <CBadge
                        color={
                          aiStatusColors[
                            aiStatus
                          ] || 'secondary'
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
                            aiAnalysis.prediction_class ===
                            1
                              ? 'danger'
                              : 'success'
                          }
                        >
                          {predictionLabels[
                            aiAnalysis
                              .prediction_label
                          ] ||
                            aiAnalysis
                              .prediction_label ||
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
                        {aiAnalysis?.model_version ||
                          '-'}
                      </div>
                    </CCol>

                    <CCol md={3}>
                      <div className="text-body-secondary small">
                        Tempo de processamento
                      </div>

                      <div>
                        {aiAnalysis?.processing_time_ms !==
                          null &&
                        aiAnalysis?.processing_time_ms !==
                          undefined
                          ? `${aiAnalysis.processing_time_ms} ms`
                          : '-'}
                      </div>
                    </CCol>
                  </CRow>

                  {aiAnalysis?.ai_notes?.trim() && (
                    <div className="mt-4">
                      <div className="text-body-secondary small mb-1">
                        Observações técnicas da IA
                      </div>

                      <div className="rounded bg-body-tertiary p-3">
                        {aiAnalysis.ai_notes}
                      </div>
                    </div>
                  )}

                  {aiStatus === 'processing' &&
                    !aiAnalysis && (
                      <CAlert
                        color="info"
                        className="d-flex align-items-center gap-2 mt-4 mb-0"
                      >
                        <CSpinner size="sm" />

                        <span>
                          A análise está sendo
                          executada. Uma segunda
                          execução permanece
                          bloqueada.
                        </span>
                      </CAlert>
                    )}

                  {aiStatus === 'failed' &&
                    !aiAnalysis && (
                      <CAlert
                        color="danger"
                        className="mt-4 mb-0"
                      >
                        A análise falhou. Restaure o
                        exame antes de realizar uma
                        nova tentativa.
                      </CAlert>
                    )}

                  {aiStatus !== 'processing' &&
                    aiStatus !== 'failed' &&
                    !aiAnalysis && (
                      <CAlert
                        color="secondary"
                        className="mt-4 mb-0"
                      >
                        Este exame ainda não possui
                        análise de IA vinculada.
                      </CAlert>
                    )}
                </>
              )}
            </section>
          </CCol>

          {reviewPanel && (
            <CCol lg={6}>
              {reviewPanel}
            </CCol>
          )}
        </CRow>
      </CCardBody>
    </CCard>
  )
}

export default ExamAiResultCard
