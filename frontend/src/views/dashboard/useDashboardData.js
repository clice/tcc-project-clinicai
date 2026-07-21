import { useEffect, useState } from 'react'

import { aiAnalysisService } from 'src/services/aiAnalysisService'
import { clinicService } from 'src/services/clinicService'
import { examService } from 'src/services/examService'
import { patientService } from 'src/services/patientService'
import { userService } from 'src/services/userService'
import { ROLES } from 'src/utils/permissions'

const emptySummary = { clinics: 0, users: 0, patients: 0, exams: 0 }
const countActive = (items) =>
  items.filter((item) => !item.status_name || item.status_name === 'active').length

export const useDashboardData = (roleName) => {
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const [exams, setExams] = useState([])
  const [summary, setSummary] = useState(emptySummary)
  const [aiMetrics, setAiMetrics] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setIsLoading(true)
        setError('')

        const [patientsData, examsData] = await Promise.all([
          patientService.list({ includeInactive: false }),
          examService.list({ includeInactive: true }),
        ])
        const patients = Array.isArray(patientsData) ? patientsData : []
        const scopedExams = Array.isArray(examsData) ? examsData : []
        const nextSummary = {
          ...emptySummary,
          patients: patients.length,
          exams: scopedExams.length,
        }

        if (isAdminMaster) {
          const [clinicsData, usersData] = await Promise.all([
            clinicService.list({ includeInactive: true }),
            userService.list({}),
          ])
          nextSummary.clinics = countActive(Array.isArray(clinicsData) ? clinicsData : [])
          nextSummary.users = countActive(Array.isArray(usersData) ? usersData : [])

          try {
            setAiMetrics(await aiAnalysisService.getMetrics())
          } catch {
            setAiMetrics(null)
          }
        }

        setExams(scopedExams)
        setSummary(nextSummary)
      } catch {
        setError('Não foi possível carregar os indicadores do dashboard.')
      } finally {
        setIsLoading(false)
      }
    }

    void loadDashboard()
  }, [isAdminMaster])

  return { exams, summary, aiMetrics, isLoading, error, isAdminMaster }
}
