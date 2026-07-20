import React, { useEffect, useState } from 'react'
import {
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CRow,
  CSpinner,
} from '@coreui/react'

import { useFeedback } from 'src/hooks/useFeedback'
import { addressService } from 'src/services/addressService'
import { clinicService } from 'src/services/clinicService'
import { getErrorMessage } from 'src/utils/errors'
import { formatCnpjBR, formatPhoneBR, formatZipCodeBR, onlyNumbers } from 'src/utils/formatters'

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

const ClinicProfileCard = ({ canUpdate = false }) => {
  const { showSuccess, showError } = useFeedback()
  const [form, setForm] = useState(emptyClinic)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingAddress, setIsLoadingAddress] = useState(false)

  useEffect(() => {
    const loadClinic = async () => {
      try {
        setIsLoading(true)
        const clinic = await clinicService.getMyClinic()
        setForm({
          name: clinic.name ?? '',
          cnpj: formatCnpjBR(clinic.cnpj ?? ''),
          email: clinic.email ?? '',
          phone: formatPhoneBR(clinic.phone ?? ''),
          mobile_phone: formatPhoneBR(clinic.mobile_phone ?? ''),
          zip_code: formatZipCodeBR(clinic.zip_code ?? ''),
          address: clinic.address ?? '',
          number: clinic.number ?? '',
          complement: clinic.complement ?? '',
          neighborhood: clinic.neighborhood ?? '',
          city: clinic.city ?? '',
          state: clinic.state ?? '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar os dados da clínica.'))
      } finally {
        setIsLoading(false)
      }
    }

    loadClinic()
  }, [showError])

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
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
    if (!canUpdate) return

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

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!canUpdate) return

    showError('')
    showSuccess('')

    if (!form.name.trim()) {
      showError('Informe o nome da clínica.')
      return
    }
    if (onlyNumbers(form.cnpj).length !== 14) {
      showError('Informe um CNPJ válido.')
      return
    }
    if (form.zip_code && onlyNumbers(form.zip_code).length !== 8) {
      showError('CEP inválido.')
      return
    }
    if (form.phone && onlyNumbers(form.phone).length < 10) {
      showError('Telefone inválido.')
      return
    }
    if (form.mobile_phone && onlyNumbers(form.mobile_phone).length < 10) {
      showError('Celular inválido.')
      return
    }
    if (form.state && form.state.trim().length !== 2) {
      showError('UF deve conter 2 caracteres.')
      return
    }

    try {
      setIsSaving(true)
      const clinic = await clinicService.updateMyClinic({
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
      setForm((current) => ({
        ...current,
        name: clinic.name,
        cnpj: formatCnpjBR(clinic.cnpj),
        email: clinic.email ?? '',
        phone: formatPhoneBR(clinic.phone ?? ''),
        mobile_phone: formatPhoneBR(clinic.mobile_phone ?? ''),
        zip_code: formatZipCodeBR(clinic.zip_code ?? ''),
        address: clinic.address ?? '',
        number: clinic.number ?? '',
        complement: clinic.complement ?? '',
        neighborhood: clinic.neighborhood ?? '',
        city: clinic.city ?? '',
        state: clinic.state ?? '',
      }))
      showSuccess('Dados da clínica atualizados com sucesso.')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao atualizar os dados da clínica.'))
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <CCard className="mb-4">
        <CCardBody className="d-flex justify-content-center py-4">
          <CSpinner />
        </CCardBody>
      </CCard>
    )
  }

  return (
    <CCard className="mb-4">
      <CCardHeader>
        <strong>Minha Clínica</strong>
      </CCardHeader>
      <CCardBody>
        <CForm onSubmit={handleSubmit}>
          <CRow className="g-3">
            <CCol md={8}>
              <CFormLabel>Nome</CFormLabel>
              <CFormInput
                value={form.name}
                disabled={!canUpdate}
                placeholder="Ex: Clínica Vida"
                onChange={(event) => updateField('name', event.target.value)}
                required
              />
            </CCol>

            <CCol md={4}>
              <CFormLabel>CNPJ</CFormLabel>
              <CFormInput
                value={form.cnpj}
                disabled={!canUpdate}
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
                disabled={!canUpdate}
                placeholder="contato@clinica.com"
                onChange={(event) => updateField('email', event.target.value)}
              />
            </CCol>

            <CCol md={4}>
              <CFormLabel>Telefone</CFormLabel>
              <CFormInput
                value={form.phone}
                disabled={!canUpdate}
                placeholder="(00) 0000-0000"
                onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
              />
            </CCol>

            <CCol md={4}>
              <CFormLabel>Celular</CFormLabel>
              <CFormInput
                value={form.mobile_phone}
                disabled={!canUpdate}
                placeholder="(00) 00000-0000"
                onChange={(event) => updateField('mobile_phone', formatPhoneBR(event.target.value))}
              />
            </CCol>

            <CCol md={2}>
              <CFormLabel>CEP</CFormLabel>
              <CFormInput
                value={form.zip_code}
                disabled={!canUpdate || isLoadingAddress}
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
                disabled={!canUpdate}
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
          </CRow>

          {canUpdate && (
            <CButton color="primary" type="submit" className="mt-4" disabled={isSaving}>
              {isSaving ? 'Salvando...' : 'Salvar dados da clínica'}
            </CButton>
          )}
        </CForm>
      </CCardBody>
    </CCard>
  )
}

export default ClinicProfileCard
