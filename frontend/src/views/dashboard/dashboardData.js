export const DASHBOARD_STATUSES = [
  'pending',
  'awaiting_review',
  'completed',
  'completed_with_divergence',
  'failed',
  'canceled',
]

export const CHART_COLORS = {
  pending: '#3399ff',
  awaiting_review: '#f9b115',
  completed: '#27c150',
  completed_with_divergence: '#4f5d73',
  failed: '#e55353',
  canceled: '#768192',
}

export const countExamsByStatus = (exams) => {
  const counts = Object.fromEntries(DASHBOARD_STATUSES.map((status) => [status, 0]))

  exams.forEach((exam) => {
    if (exam.status_name in counts) counts[exam.status_name] += 1
  })

  return counts
}

export const calculateConcordance = (counts) => {
  const reviewed = counts.completed + counts.completed_with_divergence
  return reviewed > 0 ? counts.completed / reviewed : 0
}

export const buildLastSixMonths = (exams, referenceDate = new Date()) => {
  const months = Array.from({ length: 6 }, (_, index) => {
    const date = new Date(referenceDate.getFullYear(), referenceDate.getMonth() - (5 - index), 1)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    const label = new Intl.DateTimeFormat('pt-BR', { month: 'short' }).format(date).replace('.', '')

    return { key, label, completed: 0, divergence: 0, failed: 0, canceled: 0 }
  })

  const byKey = new Map(months.map((month) => [month.key, month]))

  exams.forEach((exam) => {
    const month = exam.exam_date?.slice(0, 7)
    const bucket = byKey.get(month)
    if (!bucket) return

    if (exam.status_name === 'completed') bucket.completed += 1
    if (exam.status_name === 'completed_with_divergence') bucket.divergence += 1
    if (exam.status_name === 'failed') bucket.failed += 1
    if (exam.status_name === 'canceled') bucket.canceled += 1
  })

  return months
}
