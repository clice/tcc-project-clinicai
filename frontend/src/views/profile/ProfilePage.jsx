/**
 * Página de Perfil do usuário autenticado.
 *
 * Diferente do UserForm (que é o cadastro administrado pelo admin_master),
 * esta página é acessada por qualquer usuário logado (admin_master, doctor,
 * clinic_staff) para:
 * - visualizar e editar os próprios dados cadastrais (nome, e-mail, telefone, CPF);
 * - trocar a própria senha, exigindo a senha atual.
 *
 * Perfil de acesso, status e clínica NÃO são editáveis aqui — são
 * exclusivos do admin_master via /users/:id.
 */

import React, { useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CRow,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { userService } from 'src/services/userService'
import ClinicProfileCard from './ClinicProfileCard'

import { getErrorMessage } from 'src/utils/errors'
import { formatCpfBR, formatPhoneBR, onlyNumbers } from 'src/utils/formatters'
import { hasPermission, PERMISSIONS } from 'src/utils/permissions'

const emptyProfile = {
  name: '',
  email: '',
  cpf: '',
  phone: '',
}

const emptyPasswordForm = {
  currentPassword: '',
  password: '',
  confirmPassword: '',
}

const ProfilePage = () => {
  const { user, refreshUser } = useAuth()
  const { showSuccess, showError, startLoading, stopLoading } = useFeedback()

  const [form, setForm] = useState(emptyProfile)
  const [passwordForm, setPasswordForm] = useState(emptyPasswordForm)

  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isSavingPassword, setIsSavingPassword] = useState(false)

  useEffect(() => {
    if (!user) return

    setForm({
      name: user.name ?? '',
      email: user.email ?? '',
      cpf: formatCpfBR(user.cpf ?? ''),
      phone: formatPhoneBR(user.phone ?? ''),
    })
  }, [user])

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const updatePasswordField = (field, value) => {
    setPasswordForm((current) => ({ ...current, [field]: value }))
  }

  /**
   * Salva os dados cadastrais (nome, e-mail, telefone, CPF).
   */
  const handleProfileSubmit = async (event) => {
    event.preventDefault()

    showError('')
    showSuccess('')

    const cpfNumbers = onlyNumbers(form.cpf)

    if (!form.name.trim()) {
      showError('Informe seu nome.')
      return
    }

    if (!form.email.trim()) {
      showError('Informe seu e-mail.')
      return
    }

    if (cpfNumbers && cpfNumbers.length !== 11) {
      showError('CPF deve conter 11 números.')
      return
    }

    try {
      setIsSavingProfile(true)
      startLoading()

      await userService.updateMyProfile({
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        cpf: cpfNumbers || null,
        phone: onlyNumbers(form.phone) || null,
      })

      await refreshUser()

      showSuccess('Dados atualizados com sucesso.')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao atualizar os dados do perfil.'))
    } finally {
      setIsSavingProfile(false)
      stopLoading()
    }
  }

  /**
   * Troca a senha, exigindo a senha atual.
   */
  const handlePasswordSubmit = async (event) => {
    event.preventDefault()

    showError('')
    showSuccess('')

    if (!passwordForm.currentPassword) {
      showError('Informe sua senha atual.')
      return
    }

    if (passwordForm.password.trim().length < 8) {
      showError('A nova senha deve ter no mínimo 8 caracteres.')
      return
    }

    if (passwordForm.password !== passwordForm.confirmPassword) {
      showError('Nova senha e confirmação não coincidem.')
      return
    }

    try {
      setIsSavingPassword(true)
      startLoading()

      await userService.updateMyPassword(
        passwordForm.password.trim(),
        passwordForm.currentPassword,
      )

      setPasswordForm(emptyPasswordForm)
      showSuccess('Senha atualizada com sucesso.')
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao atualizar a senha.'))
    } finally {
      setIsSavingPassword(false)
      stopLoading()
    }
  }

  return (
    <>
      <div className="mb-4">
        <div className="text-body-secondary">Minha Conta</div>
        <h1 className="h3 mb-0">Meu Perfil</h1>
        <p className="text-body-secondary mb-0">
          Visualize e atualize seus dados cadastrais e sua senha de acesso.
        </p>
      </div>

      <CCard className="mb-4">
        <CCardHeader>
          <strong>Dados cadastrais</strong>
        </CCardHeader>

        <CCardBody>
          <CForm onSubmit={handleProfileSubmit}>
            <CRow className="g-3">
              <CCol md={8}>
                <CFormLabel>Nome</CFormLabel>
                <CFormInput
                  value={form.name}
                  onChange={(event) => updateField('name', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>E-mail</CFormLabel>
                <CFormInput
                  type="email"
                  value={form.email}
                  onChange={(event) => updateField('email', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>CPF</CFormLabel>
                <CFormInput
                  value={form.cpf}
                  onChange={(event) => updateField('cpf', formatCpfBR(event.target.value))}
                  placeholder="000.000.000-00"
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Telefone</CFormLabel>
                <CFormInput
                  value={form.phone}
                  onChange={(event) => updateField('phone', formatPhoneBR(event.target.value))}
                  placeholder="(88) 99999-9999"
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Perfil de acesso</CFormLabel>
                <CFormInput
                  value={user?.role_display_name || user?.role_name || ''}
                  disabled
                />
              </CCol>
            </CRow>

            <CButton color="primary" type="submit" className="mt-4" disabled={isSavingProfile}>
              {isSavingProfile ? 'Salvando...' : 'Salvar dados'}
            </CButton>
          </CForm>
        </CCardBody>
      </CCard>

      {user?.clinic_id && hasPermission(user, PERMISSIONS.CLINICS_READ_PROFILE) && (
        <ClinicProfileCard
          canUpdate={hasPermission(user, PERMISSIONS.CLINICS_UPDATE_PROFILE)}
        />
      )}

      <CCard className="mb-4">
        <CCardHeader>
          <strong>Alterar senha</strong>
        </CCardHeader>

        <CCardBody>
          <CAlert color="info" className="mb-3">
            Por segurança, ao trocar sua senha todas as suas sessões ativas em outros
            dispositivos serão encerradas.
          </CAlert>

          <CForm onSubmit={handlePasswordSubmit}>
            <CRow className="g-3">
              <CCol md={4}>
                <CFormLabel>Senha atual</CFormLabel>
                <CFormInput
                  type="password"
                  value={passwordForm.currentPassword}
                  autoComplete="current-password"
                  onChange={(event) => updatePasswordField('currentPassword', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Nova senha</CFormLabel>
                <CFormInput
                  type="password"
                  value={passwordForm.password}
                  autoComplete="new-password"
                  onChange={(event) => updatePasswordField('password', event.target.value)}
                  required
                />
              </CCol>

              <CCol md={4}>
                <CFormLabel>Confirmar nova senha</CFormLabel>
                <CFormInput
                  type="password"
                  value={passwordForm.confirmPassword}
                  autoComplete="new-password"
                  onChange={(event) =>
                    updatePasswordField('confirmPassword', event.target.value)
                  }
                  required
                />
              </CCol>
            </CRow>

            <CButton color="primary" type="submit" className="mt-4" disabled={isSavingPassword}>
              {isSavingPassword ? 'Salvando...' : 'Alterar senha'}
            </CButton>
          </CForm>
        </CCardBody>
      </CCard>
    </>
  )
}

export default ProfilePage
