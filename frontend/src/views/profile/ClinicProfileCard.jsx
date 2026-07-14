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
import { clinicService } from 'src/services/clinicService'
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
  status_display_name: '',
}

const ClinicProfileCard = ({ canUpdate = false }) => {
  const { showSuccess, showError } = useFeedback()
  const [form, setForm] = useState(emptyClinic)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

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
          status_display_name: clinic.status_display_name ?? clinic.status_name ?? '',
        })
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao carregar os dados da clínica.'))
      } finally {
        setIsLoading(false)
      }
    }

    loadClinic()
  }, [])

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!canUpdate) return

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
        <strong>Minha clínica</strong>
      </CCardHeader>
      <CCardBody>
        <CForm onSubmit={handleSubmit}>
          <CRow className="g-3">
            <CCol md={8}>
              <CFormLabel>Nome</CFormLabel>
              <CFormInput
                value={form.name}
                disabled={!canUpdate}
                onChange={(event) => updateField('name', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>CNPJ</CFormLabel>
              <CFormInput
                value={form.cnpj}
                disabled={!canUpdate}
                onChange={(event) => updateField('cnpj', formatCnpjBR(event.target.value))}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>E-mail</CFormLabel>
              <CFormInput
                type="email"
                value={form.email}
                disabled={!canUpdate}
                onChange={(event) => updateField('email', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>Telefone</CFormLabel>
              <CFormInput
                value={form.phone}
                disabled={!canUpdate}
                onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>Celular</CFormLabel>
              <CFormInput
                value={form.mobile_phone}
                disabled={!canUpdate}
                onChange={(event) =>
                  updateField('mobile_phone', formatPhoneBR(event.target.value))
                }
              />
            </CCol>
            <CCol md={3}>
              <CFormLabel>CEP</CFormLabel>
              <CFormInput
                value={form.zip_code}
                disabled={!canUpdate}
                onChange={(event) =>
                  updateField('zip_code', formatZipCodeBR(event.target.value))
                }
              />
            </CCol>
            <CCol md={7}>
              <CFormLabel>Endereço</CFormLabel>
              <CFormInput
                value={form.address}
                disabled={!canUpdate}
                onChange={(event) => updateField('address', event.target.value)}
              />
            </CCol>
            <CCol md={2}>
              <CFormLabel>Número</CFormLabel>
              <CFormInput
                value={form.number}
                disabled={!canUpdate}
                onChange={(event) => updateField('number', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>Complemento</CFormLabel>
              <CFormInput
                value={form.complement}
                disabled={!canUpdate}
                onChange={(event) => updateField('complement', event.target.value)}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>Bairro</CFormLabel>
              <CFormInput
                value={form.neighborhood}
                disabled={!canUpdate}
                onChange={(event) => updateField('neighborhood', event.target.value)}
              />
            </CCol>
            <CCol md={3}>
              <CFormLabel>Cidade</CFormLabel>
              <CFormInput
                value={form.city}
                disabled={!canUpdate}
                onChange={(event) => updateField('city', event.target.value)}
              />
            </CCol>
            <CCol md={1}>
              <CFormLabel>UF</CFormLabel>
              <CFormInput
                value={form.state}
                disabled={!canUpdate}
                maxLength={2}
                onChange={(event) => updateField('state', event.target.value.toUpperCase())}
              />
            </CCol>
            <CCol md={4}>
              <CFormLabel>Status</CFormLabel>
              <CFormInput value={form.status_display_name} disabled />
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
