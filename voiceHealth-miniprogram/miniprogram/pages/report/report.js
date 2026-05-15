// pages/report/report.js
const app = getApp()
const { getRiskColor, getRiskText, formatTime } = require('../../utils/util.js')

Page({
  data: {
    reportId: '',
    report: null,
    loading: true,
    error: false,
    errorMsg: '',
    scoreLevel: '',
    scoreColor: '',
    analysisType: 'voice' // voice, face, video, combined
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ reportId: options.id })
      this.loadReport(options.id)
    } else {
      this.setData({ loading: false, error: true, errorMsg: '缺少报告ID参数' })
    }
  },

  onShow() {
    // Refresh if needed
  },

  // 加载报告数据
  async loadReport(id) {
    this.setData({ loading: true, error: false })
    try {
      const res = await app.request({ url: `/api/v1/report/${id}` })
      // Handle various API response formats
      if (res) {
        const report = res.report || res
        if (report && (report.overallScore !== undefined || report.score !== undefined)) {
          this.processReport(report)
          return
        }
      }
      // If API returns no valid data, show error
      this.setData({
        loading: false,
        error: true,
        errorMsg: '报告不存在或已过期'
      })
    } catch (err) {
      console.error('加载报告失败:', err)
      // Try loading from local cache
      const cached = wx.getStorageSync(`report_${id}`)
      if (cached) {
        this.processReport(cached)
        return
      }
      this.setData({
        loading: false,
        error: true,
        errorMsg: err.message || '网络错误，请稍后重试'
      })
    }
  },

  // 重试加载
  retryReport() {
    if (this.data.reportId) {
      this.loadReport(this.data.reportId)
    }
  },

  // 处理报告数据
  processReport(report) {
    // Normalize score field
    const overallScore = report.overallScore || report.score || 0
    report.overallScore = overallScore

    // Determine score level and color
    let scoreLevel = 'normal'
    let scoreColor = '#3b82f6'
    if (overallScore >= 85) { scoreLevel = 'excellent'; scoreColor = '#22c55e' }
    else if (overallScore >= 70) { scoreLevel = 'good'; scoreColor = '#3b82f6' }
    else if (overallScore >= 50) { scoreLevel = 'fair'; scoreColor = '#eab308' }
    else { scoreLevel = 'poor'; scoreColor = '#ef4444' }

    // Format dates
    const createdAt = report.createdAt || report.created_at || report.date || new Date().toISOString()
    const d = new Date(createdAt)
    report.dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    report.timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`

    // Determine analysis type
    const analysisType = report.analysisType || report.analysis_type || report.type || 'voice'

    // Normalize acoustic features
    if (report.acousticFeatures || report.acoustic_features) {
      const features = report.acousticFeatures || report.acoustic_features
      report.acousticFeatures = features.map(f => ({
        name: f.name || f.label || '未知',
        score: f.score || f.value || 0,
        icon: f.icon || this.getFeatureIcon(f.name || f.label),
        desc: f.desc || f.description || f.detail || ''
      }))
    }

    // Normalize risk assessment
    if (report.riskAssessment || report.risk_assessment || report.risks) {
      const risks = report.riskAssessment || report.risk_assessment || report.risks
      report.riskAssessment = risks.map(r => ({
        category: r.category || r.name || '未知',
        level: r.level || r.risk_level || 'low',
        score: r.score || r.value || 0,
        desc: r.desc || r.description || r.detail || ''
      }))
    }

    // Normalize AI advice
    if (report.aiAdvice || report.ai_advice || report.suggestions || report.advice) {
      const advice = report.aiAdvice || report.ai_advice || report.suggestions || report.advice
      report.aiAdvice = advice.map(a => ({
        title: a.title || a.name || '建议',
        content: a.content || a.text || a.detail || '',
        icon: a.icon || this.getAdviceIcon(a.title || a.name)
      }))
    }

    // Cache the report locally
    wx.setStorageSync(`report_${this.data.reportId}`, report)

    this.setData({
      report,
      loading: false,
      error: false,
      scoreLevel,
      scoreColor,
      analysisType
    })
  },

  // Get feature icon by name
  getFeatureIcon(name) {
    const iconMap = {
      '基频': '🎵', '呼吸': '💨', '语速': '⏱️', '清晰': '🔊',
      '情感': '😊', '疲劳': '😴', '音调': '🎶', '音量': '📢',
      '皱纹': '〰️', '色斑': '🔵', '紧致': '💪', '眼部': '👁️',
      '法令纹': '😊', '肤色': '🎨'
    }
    for (const [key, icon] of Object.entries(iconMap)) {
      if (name && name.includes(key)) return icon
    }
    return '📊'
  },

  // Get advice icon by title
  getAdviceIcon(title) {
    const iconMap = {
      '呼吸': '🫁', '嗓子': '💧', '休息': '😴', '检测': '📊',
      '运动': '🏃', '饮食': '🥗', '睡眠': '🌙', '防晒': '☀️'
    }
    for (const [key, icon] of Object.entries(iconMap)) {
      if (title && title.includes(key)) return icon
    }
    return '💡'
  },

  // 分享报告
  onShareAppMessage() {
    return {
      title: `我的健康评分: ${this.data.report?.overallScore || '--'}分`,
      path: `/pages/report/report?id=${this.data.reportId}`
    }
  },

  // 显示分享选项
  shareReport() {
    wx.showActionSheet({
      itemList: ['分享给好友', '保存图片'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // Trigger share via button
        } else if (res.tapIndex === 1) {
          this.saveReportImage()
        }
      }
    })
  },

  // 保存报告图片
  saveReportImage() {
    wx.showToast({ title: '图片生成中...', icon: 'loading' })
    // Use canvas to generate report image
    // For now, show a placeholder
    setTimeout(() => {
      wx.showToast({ title: '功能开发中', icon: 'none' })
    }, 1000)
  },

  // 返回
  goBack() {
    wx.navigateBack({
      fail: () => {
        wx.switchTab({ url: '/pages/index/index' })
      }
    })
  },

  // 查看历史记录
  goHistory() {
    wx.switchTab({ url: '/pages/history/history' })
  }
})
