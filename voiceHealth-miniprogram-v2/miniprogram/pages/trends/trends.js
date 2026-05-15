// pages/trends/trends.js
const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    loading: true,
    error: false,
    trends: [],
    avgScore: '--',
    bestScore: '--',
    latestScore: '--',
    days: 30,
    typeMap: {
      voice: { icon: '🎤', text: '语音' },
      face: { icon: '📸', text: '面部' },
      video: { icon: '🎬', text: '视频' },
      combined: { icon: '📊', text: '综合' }
    }
  },

  onLoad() {
    this.loadTrends()
  },

  onPullDownRefresh() {
    this.loadTrends().finally(() => wx.stopPullDownRefresh())
  },

  async loadTrends() {
    this.setData({ loading: true, error: false })
    try {
      const res = await app.request({ url: `/api/v1/trends?days=${this.data.days}` })
      const rows = res.trends || []
      const scores = rows.map(item => Number(item.score || 0)).filter(score => score > 0)
      const trends = rows.map(item => this.formatTrend(item))

      this.setData({
        trends,
        avgScore: scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : '--',
        bestScore: scores.length ? Math.round(Math.max(...scores)) : '--',
        latestScore: scores.length ? Math.round(scores[scores.length - 1]) : '--',
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false, error: true })
      wx.showToast({ title: '趋势加载失败', icon: 'none' })
    }
  },

  formatTrend(item) {
    const score = Math.round(item.score || 0)
    const type = item.type || 'voice'
    const meta = this.data.typeMap[type] || this.data.typeMap.voice
    const level = util.getScoreLevel(score)
    return {
      score,
      type,
      icon: meta.icon,
      typeText: meta.text,
      date: util.formatDate(item.date),
      barWidth: `${Math.max(8, score)}%`,
      color: level.color,
      levelText: level.text
    }
  },

  retryLoad() {
    this.loadTrends()
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth健康趋势', path: '/pages/trends/trends' }
  }
})
