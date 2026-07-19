/**
 * Tela de login do ClinicAI.
 *
 * Responsável por:
 * - capturar e-mail e senha;
 * - autenticar o usuário na API;
 * - buscar os dados do usuário logado;
 * - redirecionar para o dashboard.
 */

import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardGroup,
  CCol,
  CContainer,
  CForm,
  CFormInput,
  CInputGroup,
  CInputGroupText,
  CRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilLockLocked, cilUser } from '@coreui/icons'

import { useAuth } from 'src/hooks/useAuth'

const Login = () => {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    email: '',
    password: '',
  })

  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const updateField = (field, value) => {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.message ||
        'Não foi possível realizar o login. Verifique suas credenciais.'

    setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-body-tertiary min-vh-100 d-flex flex-row align-items-center">
      <CContainer>
        <CRow className="justify-content-center">
          <CCol md={8}>
            <CCardGroup>
              <CCard className="p-4">
                <CCardBody>
                  <CForm onSubmit={handleSubmit}>
                    <h1>Login</h1>
                    <p className="text-body-secondary">Entre com sua conta para acessar o ClinicAI</p>

                    {error && <CAlert color="danger">{error}</CAlert>}

                    <CInputGroup className="mb-3">
                      <CInputGroupText>
                        <CIcon icon={cilUser} />
                      </CInputGroupText>

                      <CFormInput
                        type="email"
                        placeholder="E-mail"
                        autoComplete="email"
                        value={form.email}
                        onChange={(event) => updateField('email', event.target.value)}
                        required
                      />
                    </CInputGroup>

                    <CInputGroup className="mb-4">
                      <CInputGroupText>
                        <CIcon icon={cilLockLocked} />
                      </CInputGroupText>

                      <CFormInput
                        type="password"
                        placeholder="Senha"
                        autoComplete="current-password"
                        value={form.password}
                        onChange={(event) => updateField('password', event.target.value)}
                        required
                      />
                    </CInputGroup>

                    <CRow>
                      <CCol xs={12}>
                        <CButton
                          color="primary"
                          className="clinicai-btn px-4"
                          type="submit"
                          disabled={isLoading}
                        >
                          {isLoading ? 'Entrando...' : 'Entrar'}
                        </CButton>
                      </CCol>
                    </CRow>
                  </CForm>
                </CCardBody>
              </CCard>

              <CCard
                className="clinicai-login-brand-panel text-white py-5"
                style={{ width: '44%' }}
              >
                <CCardBody className="text-center">
                  <div>
                    <h2>ClinicAI</h2>
                    <p>
                      Sistema web para gestão clínica e apoio à análise de exames utilizando 
                      inteligência artificial.
                    </p>
                  </div>
                </CCardBody>
              </CCard>
            </CCardGroup>
          </CCol>
        </CRow>
      </CContainer>
    </div>
  )
}

export default Login
