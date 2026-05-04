/**
 * Formulário do módulo de Clinics.
 *
 * Usado para:
 * - criar clínica;
 * - visualizar clínica;
 * - editar clínica.
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
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormTextarea,
  CRow,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'

import { addressService } from 'src/services/addressService'
import { clinicService } from 'src/services/clinicService'
import { statusService } from 'src/services/statusService'

import { getErrorMessage } from 'src/utils/errors'
import {
  formatCnpjBR,
  formatPhoneBR,
  formatZipCodeBR,
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
  status_id: '',
}

const ClinicForm = ({ mode = 'create' }) => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyClinic)
  const [statuses, setStatuses] = useState([])
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingAddress, setIsLoadingAddress] = useState(false)

  const isReadOnly = mode === 'view'
  const isCreateMode = mode === 'create'
  const isEditMode = mode === 'edit'

  const title = useMemo(() => {
    if (isCreateMode) return 'Cadastrar Clínica'
    if (isEditMode) return 'Editar Clínica'
    return 'Detalhes da Clínica'
  }, [isCreateMode, isEditMode])

  useEffect(() => {
    const loadPageData = async () => {
      try {
        startLoading()
        showError('')

        const statusData = await statusService.list()

        /**
         * O backend valida que a clínica use apenas status com applies_to = clinic.
         */
        setStatuses(
          Array.isArray(statusData)
            ? statusData.filter((status) => status.applies_to === 'clinic')
            : [],
        )

        if (!isCreateMode) {
          const clinicData = await clinicService.getById(id)

          setForm({
            name: clinicData.name ?? '',
            cnpj: clinicData.cnpj ? formatCnpjBR(clinicData.cnpj) : '',
            email: clinicData.email ?? '',
            phone: clinicData.phone ? formatPhoneBR(clinicData.phone) : '',
            mobile_phone: clinicData.mobile_phone
              ? formatPhoneBR(clinicData.mobile_phone)
              : '',
            zip_code: clinicData.zip_code ? formatZipCodeBR(clinicData.zip_code) : '',
            address: clinicData.address ?? '',
            number: clinicData.number ?? '',
            complement: clinicData.complement ?? '',
            neighborhood: clinicData.neighborhood ?? '',
            city: clinicData.city ?? '',
            state: clinicData.state ?? '',
            status_id: clinicData.status_id ?? '',
          })
        }
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar dados da clínica.'))
      } finally {
        stopLoading()
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

  /**
   * Valida campos obrigatórios antes de enviar ao backend.
   */
  const validateForm = () => {
    if (!form.name.trim()) {
      showError('Informe o nome da clínica.')
      return false
    }

    if (onlyNumbers(form.cnpj).length !== 14) {
      showError('Informe um CNPJ válido.')
      return false
    }

    if (!form.status_id) {
      showError('Selecione o status da clínica.')
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
  const buildPayload = () => {
    const status = statuses.find((item) => String(item.id) === String(form.status_id))

    return {
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
      status_id: Number(form.status_id),
      status_name: status?.name ?? null,
      status_display_name: status?.display_name ?? null,
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isReadOnly) return

    showError('')
    showSuccess('')

    if (!validateForm()) return

    try {
      setIsSaving(true)

      if (isCreateMode) {
        const created = await clinicService.create(buildPayload())
        navigate(`/clinics/${created.id}`)
        return
      }

      if (isEditMode) {
        await clinicService.update(id, buildPayload())
        showSuccess('Clínica atualizada com sucesso.')
      }
    } catch (err) {
      showError(err.response?.data?.detail || 'Erro ao salvar clínica.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Administração</div>
          <h1 className="h3 mb-0">{title}</h1>
          <p className="text-body-secondary mb-0">
            Cadastro usado para vincular usuários, pacientes e exames.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="secondary" size="lg" variant="outline" as={Link} to="/clinics">
            Voltar
          </CButton>
        </div> 
      </div>

      <CCard>
        <CCardHeader>
          <strong>Dados da Clínica</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleSubmit}>
            <CRow className="g-3">
              <CCol md={8}>
                <CFormLabel>Nome</CFormLabel>
                <CFormInput
                  value={form.name}
                  disabled={isReadOnly}
                  placeholder="Ex: Clínica Vida"
                  onChange={(event) => updateField('name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={2}>
                <CFormLabel>CNPJ</CFormLabel>
                <CFormInput
                  value={form.cnpj}
                  disabled={isReadOnly}
                  placeholder="00.000.000/0000-00"
                  onChange={(event) => updateField('cnpj', formatCnpjBR(event.target.value))}
                  required
                />
              </CCol>

              <CCol md={2}>
                <CFormLabel>Status</CFormLabel>
                <CFormSelect
                  value={form.status_id}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('status_id', event.target.value)}
                  required
                >
                  <option value="">Selecione...</option>

                  {statuses.map((status) => (
                    <option key={status.id} value={status.id}>
                      {status.display_name}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={4}>
                <CFormLabel>E-mail</CFormLabel>
                <CFormInput
                  type="email"
                  value={form.email}
                  disabled={isReadOnly}
                  placeholder="contato@clinica.com"
                  onChange={(event) => updateField('email', event.target.value)}
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Telefone</CFormLabel>
                <CFormInput
                  value={form.phone}
                  disabled={isReadOnly}
                  placeholder="(00) 0000-0000"
                  onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Celular</CFormLabel>
                <CFormInput
                  value={form.mobile_phone}
                  disabled={isReadOnly}
                  placeholder="(00) 00000-0000"
                  onChange={(event) =>
                    updateField('mobile_phone', formatPhoneBR(event.target.value))
                  }
                />
              </CCol>

              <CCol md={3}>
                <CFormLabel>CEP</CFormLabel>
                <CFormInput
                  value={form.zip_code}
                  disabled={isReadOnly || isLoadingAddress}
                  onChange={(event) =>
                    updateField('zip_code', formatZipCodeBR(event.target.value))
                  }
                  onBlur={handleZipCodeBlur}
                  placeholder="00000-000"
                />
              </CCol>

              <CCol md={8}>
                <CFormLabel>Endereço</CFormLabel>
                <CFormInput value={form.address} disabled />
              </CCol>

              <CCol md={1}>
                <CFormLabel>Número</CFormLabel>
                <CFormInput
                  value={form.number}
                  disabled={isReadOnly}
                  onChange={(event) => updateField('number', event.target.value)}
                />
              </CCol>

              <CCol md={6}>
                <CFormLabel>Complemento</CFormLabel>
                <CFormInput value={form.complement} disabled />
              </CCol>

              <CCol md={2}>
                <CFormLabel>Bairro</CFormLabel>
                <CFormInput value={form.neighborhood} disabled />
              </CCol>

              <CCol md={2}>
                <CFormLabel>Cidade</CFormLabel>
                <CFormInput value={form.city} disabled />
              </CCol>

              <CCol md={2}>
                <CFormLabel>UF</CFormLabel>
                <CFormInput value={form.state} disabled />
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

            {!isReadOnly && (
              <CButtonGroup className="mt-4">
                <CButton color="primary" type="submit" disabled={isSaving}>
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </CButton>

                <CButton color="secondary" variant="outline" as={Link} to="/clinics">
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

export default ClinicForm