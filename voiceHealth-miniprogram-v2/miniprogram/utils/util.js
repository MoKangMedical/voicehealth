// utils/util.js
// VoiceHealth 工具函数

const formatTime = date => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

const formatNumber = n => {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

const formatDuration = seconds => {
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return `${formatNumber(min)}:${formatNumber(sec)}`
}

const formatDate = dateStr => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const getRiskColor = level => {
  const colors = { 'low': '#22c55e', 'medium': '#eab308', 'high': '#ef4444' }
  return colors[level] || '#6b7280'
}

const getRiskText = level => {
  const texts = { 'low': '低风险', 'medium': '中等风险', 'high': '高风险' }
  return texts[level] || '未知'
}

const getScoreLevel = score => {
  if (score >= 90) return { text: '优秀', color: '#22c55e' }
  if (score >= 80) return { text: '良好', color: '#3b82f6' }
  if (score >= 70) return { text: '一般', color: '#eab308' }
  if (score >= 60) return { text: '较差', color: '#f97316' }
  return { text: '异常', color: '#ef4444' }
}

module.exports = {
  formatTime,
  formatNumber,
  formatDuration,
  formatDate,
  getRiskColor,
  getRiskText,
  getScoreLevel
}
