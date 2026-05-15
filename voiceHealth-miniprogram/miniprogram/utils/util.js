const formatTime = date => {
  const y = date.getFullYear(),
    m = date.getMonth() + 1,
    d = date.getDate(),
    h = date.getHours(),
    min = date.getMinutes(),
    s = date.getSeconds()
  return `${[y, m, d].map(n => n.toString().padStart(2, '0')).join('/')} ${[h, min, s].map(n => n.toString().padStart(2, '0')).join(':')}`
}

const formatDate = dateStr => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '--'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const formatDateShort = dateStr => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '--'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const formatDuration = s => {
  const m = Math.floor(s / 60),
    sec = s % 60
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
}

const getRiskColor = level => ({
  low: '#22c55e',
  medium: '#eab308',
  high: '#ef4444'
}[level] || '#6b7280')

const getRiskText = level => ({
  low: '低风险',
  medium: '中等风险',
  high: '高风险'
}[level] || '未知')

const getScoreColor = score => {
  if (score >= 85) return '#22c55e'
  if (score >= 70) return '#3b82f6'
  if (score >= 50) return '#eab308'
  return '#ef4444'
}

const getScoreLevel = score => {
  if (score >= 85) return 'excellent'
  if (score >= 70) return 'good'
  if (score >= 50) return 'fair'
  return 'poor'
}

const getScoreText = score => {
  if (score >= 85) return '优秀'
  if (score >= 70) return '良好'
  if (score >= 50) return '一般'
  return '需关注'
}

const getScoreSummary = score => {
  if (score >= 85) return '各项指标优秀，继续保持'
  if (score >= 70) return '整体健康状态良好'
  if (score >= 50) return '部分指标需关注'
  return '建议及时改善生活习惯'
}

module.exports = {
  formatTime,
  formatDate,
  formatDateShort,
  formatDuration,
  getRiskColor,
  getRiskText,
  getScoreColor,
  getScoreLevel,
  getScoreText,
  getScoreSummary
}
