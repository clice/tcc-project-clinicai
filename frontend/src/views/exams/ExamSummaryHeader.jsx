import React from 'react'

import { calculateAge } from 'src/utils/calculators'
import { examTypeLabels } from 'src/utils/constants'
import { formatDateBR } from 'src/utils/formatters'

const ExamSummaryHeader = ({ patientName, patientCpf, patientBirthDate, examType, examDate }) => {
  const age = calculateAge(patientBirthDate, examDate)

  const resolvedPatientName =
    patientName && patientName !== '-' ? patientName : 'Paciente não informado'

  const resolvedPatientCpf =
    patientCpf && patientCpf !== '-' ? `${patientCpf}` : 'CPF não informado'

  const resolvedAge = age !== '-' ? `${age} anos` : 'Idade não informada'

  const resolvedType = examTypeLabels[examType] || examType || 'Tipo não informado'

  const resolvedDate = examDate ? formatDateBR(examDate) : 'Data não informada'

  return (
    <div className="d-flex flex-column flex-xl-row justify-content-between align-items-xl-center gap-2 w-100">
      <div className="d-flex flex-wrap align-items-center gap-2">
        <strong>{resolvedPatientName}</strong>

        <span className="text-body-secondary fw-normal">{resolvedPatientCpf}</span>

        <span className="text-body-secondary fw-normal" aria-hidden="true">
          •
        </span>

        <span className="text-body-secondary fw-normal">{resolvedAge}</span>
      </div>

      <div className="d-flex flex-wrap align-items-center gap-2 fw-normal">
        <span>{resolvedType}</span>

        <span className="text-body-secondary" aria-hidden="true">
          •
        </span>

        <span>{resolvedDate}</span>
      </div>
    </div>
  )
}

export default ExamSummaryHeader
