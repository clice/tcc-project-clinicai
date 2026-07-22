/**
 * Formulário do módulo de Clinics.
 *
 * Usado para:
 * - criar clínica;
 * - editar clínica.
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
  CFormTextarea,
  CRow,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'

import { addressService } from 'src/services/addressService'
import { clinicService } from 'src/services/clinicService'

import { getErrorMessage } from 'src/utils/errors'
import {
  formatCnpjBR,
  formatPhoneBR,
  formatZipCodeBR,
  isValidCnpj,
  onlyNumbers,
} from 'src/utils/formatters'

const emptyClinic = {
  name: '',
  cnpj: '',
  email: '',
  phone: '',
  mobile_phone: '',
  zip_code: '',
  address: '',
  number: '',
  complement: '',
  neighborhood: '',
  city: '',
  state: '',
}

const ClinicForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyClinic)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingAddress, setIsLoadingAddress] = useState(false)

  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const title = useMemo(
    () => (isCreateMode ? 'Cadastrar Clínica' : 'Editar Clínica'),
    [isCreateMode],
  )

  useEffect(() => {
    const loadPageData = async () => {
      try {
        startLoading()
        showError('')

        if (!isCreateMode) {
          const clinicData = await clinicService.getById(id)

          setForm({
            name: clinicData.name ?? '',
            cnpj: clinicData.cnpj ? formatCnpjBR(clinicData.cnpj) : '',
            email: clinicData.email ?? '',
            phone: clinicData.phone ? formatPhoneBR(clinicData.phone) : '',
            mobile_phone: clinicData.mobile_phone ? formatPhoneBR(clinicData.mobile_phone) : '',
            zip_code: clinicData.zip_code ? formatZipCodeBR(clinicData.zip_code) : '',
            address: clinicData.address ?? '',
            number: clinicData.number ?? '',
            complement: clinicData.complement ?? '',
            neighborhood: clinicData.neighborhood ?? '',
            city: clinicData.city ?? '',
            state: clinicData.state ?? '',
          })
        }
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados da clínica.'))
      } finally {
        stopLoading()
      }
    }

    loadPageData()
  }, [id, isCreateMode, showError, startLoading, stopLoading])

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
   * Valida campos obrigatórios antes de enviar ao backend.
   */
  const validateForm = () => {
    if (!form.name.trim()) {
      showError('Informe o nome da clínica.')
      return false
    }

    if (!isValidCnpj(form.cnpj)) {
      showError('Informe um CNPJ válido.')
      return false
    }

    if (form.zip_code && onlyNumbers(form.zip_code).length !== 8) {
      showError('CEP inválido.')
      return false
    }

    if (form.phone && onlyNumbers(form.phone).length < 10) {
      showError('Telefone inválido.')
      return false
    }

    if (form.mobile_phone && onlyNumbers(form.mobile_phone).length < 10) {
      showError('Celular inválido.')
      return false
    }

    if (form.state && form.state.trim().length !== 2) {
      showError('UF deve conter 2 caracteres.')
      return false
    }

    return true
  }

  const clearAddressFields = () => {
    setForm((current) => ({
      ...current,
      address: '',
      complement: '',
      neighborhood: '',
      city: '',
      state: '',
    }))
  }

  const handleZipCodeBlur = async () => {
    const zipCode = onlyNumbers(form.zip_code)

    if (!zipCode || zipCode.length !== 8) {
      return
    }

    try {
      setIsLoadingAddress(true)
      showError('')

      clearAddressFields()

      const address = await addressService.getAddressByZipCode(zipCode)

      if (!address) {
        showError('CEP não encontrado.')
        return
      }

      setForm((current) => ({
        ...current,
        zip_code: formatZipCodeBR(address.zip_code),
        address: address.address,
        complement: address.complement,
        neighborhood: address.neighborhood,
        city: address.city,
        state: address.state,
      }))
    } catch {
      showError('Erro ao buscar endereço pelo CEP.')
    } finally {
      setIsLoadingAddress(false)
    }
  }

  /**
   * Monta o payload no formato esperado pela API.
   */
  const buildPayload = () => ({
    name: form.name.trim(),
    cnpj: onlyNumbers(form.cnpj),
    email: form.email.trim().toLowerCase() || null,
    phone: onlyNumbers(form.phone) || null,
    mobile_phone: onlyNumbers(form.mobile_phone) || null,
    zip_code: onlyNumbers(form.zip_code) || null,
    address: form.address.trim() || null,
    number: form.number.trim() || null,
    complement: form.complement.trim() || null,
    neighborhood: form.neighborhood.trim() || null,
    city: form.city.trim() || null,
    state: form.state.trim().toUpperCase() || null,
  })

  const handleSubmit = async (event) => {
    event.preventDefault()

    showError('')
    showSuccess('')

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        const created = await clinicService.create(buildPayload())
        navigate(`/clinics/${created.id}/edit`)
        return
      }

      if (isEditMode) {
        await clinicService.update(id, buildPayload())
        showSuccess('Clínica atualizada com sucesso.')
      }
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao salvar clínica.'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Administração</div>
          <h1 className="h3 mb-0 clinicai-page-title">{title}</h1>
          <p className="text-body-secondary mb-0">
            Cadastro usado para vincular usuários, pacientes e exames.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton
            color="secondary"
            size="lg"
            variant="outline"
            className="clinicai-soft-action"
            as={Link}
            to="/clinics"
          >
            Voltar
          </CButton>
        </div>
      </div>

      {isEditMode && (
        <CAlert color="info">
          Esta tela permite alterar os dados da clínica. Revise as informações antes de selecionar
          “Salvar”.
        </CAlert>
      )}

      <CCard className="clinicai-card mb-4">
        <CCardHeader className="clinicai-card-header">
          <strong>Dados da Clínica</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={8}>
                <CFormLabel>Nome</CFormLabel>
                <CFormInput
                  value={form.name}
                  placeholder="Ex: Clínica Vida"
                  onChange={(event) => updateField('name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>CNPJ</CFormLabel>
                <CFormInput
                  value={form.cnpj}
                  placeholder="00.000.000/0000-00"
                  onChange={(event) => updateField('cnpj', formatCnpjBR(event.target.value))}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>E-mail</CFormLabel>
                <CFormInput
                  type="email"
                  value={form.email}
                  placeholder="contato@clinica.com"
                  onChange={(event) => updateField('email', event.target.value)}
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Telefone</CFormLabel>
                <CFormInput
                  value={form.phone}
                  placeholder="(00) 0000-0000"
                  onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Celular</CFormLabel>
                <CFormInput
                  value={form.mobile_phone}
                  placeholder="(00) 00000-0000"
                  onChange={(event) =>
                    updateField('mobile_phone', formatPhoneBR(event.target.value))
                  }
                />
              </CCol>

              <CCol md={2}>
                <CFormLabel>CEP</CFormLabel>
                <CFormInput
                  value={form.zip_code}
                  disabled={isLoadingAddress}
                  onChange={(event) => updateField('zip_code', formatZipCodeBR(event.target.value))}
                  onBlur={handleZipCodeBlur}
                  placeholder="00000-000"
                />
              </CCol>

              <CCol md={8}>
                <CFormLabel>Endereço</CFormLabel>
                <CFormInput value={form.address} disabled />
              </CCol>

              <CCol md={2}>
                <CFormLabel>Número</CFormLabel>
                <CFormInput
                  value={form.number}
                  onChange={(event) => updateField('number', event.target.value)}
                />
              </CCol>

              <CCol md={10}>
                <CFormLabel>Complemento</CFormLabel>
                <CFormInput value={form.complement} disabled />
              </CCol>

              <CCol md={2}>
                <CFormLabel>UF</CFormLabel>
                <CFormInput value={form.state} disabled />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Bairro</CFormLabel>
                <CFormInput value={form.neighborhood} disabled />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Cidade</CFormLabel>
                <CFormInput value={form.city} disabled />
              </CCol>

              <CCol md={12}>
                <CFormLabel>Observações</CFormLabel>
                <CFormTextarea
                  rows={2}
                  disabled
                  value="O cadastro da clínica será usado depois para vincular usuários, pacientes e exames."
                />
              </CCol>
            </CRow>

            <div className="d-flex flex-wrap align-items-center mt-4 gap-2">
              <CButton color="primary" type="submit" disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Salvar'}
              </CButton>

              <CButton className="clinicai-modal-cancel-action" variant="outline" as={Link} to="/clinics">
                Cancelar
              </CButton>
            </div>
          </CForm>
        </CCardBody>
      </CCard>
    </>
  )
}

export default ClinicForm
