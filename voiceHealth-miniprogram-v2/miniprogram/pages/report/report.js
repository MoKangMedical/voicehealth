// pages/report/report.js
const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    reportId: '',
    report: null,
    loading: true,
    error: false,
    errorMsg: '',
    scoreLevel: '',
    scoreColor: '#3b82f6',
    analysisType: 'voice',
    typeText: '语音分析',
    typeIcon: '🎤'
  },

  onLoad(options) {
    if (!options.id) {
      this.setData({ loading: false, error: true, errorMsg: '缺少报告ID' })
      return
    }

    this.setData({ reportId: options.id })
    this.loadReport(options.id)
  },

  async loadReport(id) {
    this.setData({ loading: true, error: false })
    try {
      const res = await app.request({ url: `/api/v1/report/${id}` })
      if (res && res.ok && res.report) {
        this.processReport(res.report)
        return
      }
      throw new Error('报告不存在')
    } catch (err) {
      const cached = wx.getStorageSync(`report_${id}`)
      if (cached) {
        this.processReport(cached)
        return
      }
      this.setData({
        loading: false,
        error: true,
        errorMsg: err.message || '报告加载失败'
      })
    }
  },

  processReport(rawReport) {
    const report = this.normalizeReport(rawReport)
    const level = util.getScoreLevel(report.overallScore)

    wx.setStorageSync(`report_${this.data.reportId}`, report)
    this.setData({
      report,
      loading: false,
      error: false,
      scoreLevel: level.text,
      scoreColor: level.color,
      analysisType: report.analysisType,
      typeText: this.getTypeText(report.analysisType),
      typeIcon: this.getTypeIcon(report.analysisType)
    })
  },

  normalizeReport(raw) {
    const report = { ...raw }
    const type = report.analysisType || report.analysis_type || report.type || 'voice'
    const score = report.overallScore || report.overall_score || report.score || 0
    const createdAt = report.createdAt || report.created_at || report.date || new Date().toISOString()

    report.analysisType = type
    report.overallScore = Math.round(score)
    report.dateText = this.formatDateTime(createdAt)
    report.summary = report.summary || report.overallDesc || this.getScoreSummary(report.overallScore)

    const features = report.acousticFeatures || report.acoustic_features || report.features || []
    report.acousticFeatures = features.map(item => ({
      name: item.name || item.label || '声学指标',
      score: Math.round(item.score || item.percent || 0),
      value: item.value || '',
      desc: item.desc || item.description || '',
      color: this.getScoreColor(item.score || item.percent || 0)
    }))

    const domains = report.voiceDomains || report.voice_domains || report.domains || []
    report.voiceDomains = domains.map(item => {
      const domainScore = Math.round(item.score || 0)
      return {
        name: item.name || '健康维度',
        score: domainScore,
        level: item.level || this.getDomainLevel(domainScore),
        desc: item.desc || item.description || '',
        color: this.getScoreColor(domainScore)
      }
    })

    const quality = report.voiceQuality || report.voice_quality || {}
    report.voiceQuality = quality
    report.voiceQualityItems = this.formatVoiceQuality(quality)

    const risks = report.riskAssessment || report.risk_assessment || report.risks || []
    report.riskAssessment = risks.map(item => ({
      id: item.id || item.key || '',
      name: item.name || item.category || '健康风险',
      category: item.name || item.category || '健康风险',
      group: item.category || item.group || '',
      level: item.level || 'low',
      score: Math.round(item.score || this.getRiskScore(item.level || 'low')),
      levelText: item.levelText || item.level_text || util.getRiskText(item.level || 'low'),
      color: this.getRiskColor(item.level || 'low'),
      desc: item.desc || item.description || '',
      suggestion: item.suggestion || '',
      markerText: this.formatMarkers(item.markers || item.marker)
    }))

    const advice = report.aiAdvice || report.ai_advice || report.suggestions || []
    if (Array.isArray(advice)) {
      report.aiAdvice = advice.map(item => {
        if (typeof item === 'string') {
          return { title: '健康建议', content: item, icon: '💡' }
        }
        return {
          title: item.title || item.name || '健康建议',
          content: item.content || item.text || item.detail || '',
          icon: item.icon || '💡'
        }
      })
    } else if (report.ai_insight) {
      report.aiAdvice = [{ title: '健康建议', content: report.ai_insight, icon: '💡' }]
    } else {
      report.aiAdvice = []
    }

    report.predictedAge = report.predictedAge || report.predicted_age || report.biologicalAge || report.biological_age
    report.dimensions = (report.dimensions || []).map(item => ({
      ...item,
      score: Math.round(item.score || 0),
      color: this.getScoreColor(item.score || 0)
    }))
    report.skin = report.skin || report.skin_result
    report.eye = report.eye || report.eye_result
    report.hair = report.hair || report.hair_result
    report.videoItems = [
      this.formatVideoItem('皮肤状态', '🧴', report.skin),
      this.formatVideoItem('眼睛状态', '👁️', report.eye),
      this.formatVideoItem('头发状态', '💇', report.hair)
    ].filter(Boolean)
    report.livenessPercent = Math.round((report.liveness_score || 0) * 100)
    report.readingPercent = Math.round((report.reading_match_score || 0) * 100)
    report.improvementPlan = this.normalizeActionPlan(report.improvementPlan || report.actionPlan)

    return report
  },

  normalizeActionPlan(plan) {
    if (!plan || !Array.isArray(plan.actions)) {
      return { actions: [], goals: [], problemSignals: [], whenToSeekCare: [] }
    }

    const priorityMeta = {
      high: { text: '优先', color: '#ef4444' },
      medium: { text: '建议', color: '#f59e0b' },
      low: { text: '保持', color: '#22c55e' }
    }

    return {
      ...plan,
      goals: plan.goals || [],
      problemSignals: plan.problemSignals || [],
      whenToSeekCare: plan.whenToSeekCare || [],
      actions: plan.actions.map(item => {
        const meta = priorityMeta[item.priority] || priorityMeta.medium
        return {
          ...item,
          priorityText: meta.text,
          priorityColor: meta.color,
          steps: item.steps || []
        }
      })
    }
  },

  formatDateTime(dateStr) {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '--'
    return `${date.getFullYear()}-${util.formatNumber(date.getMonth() + 1)}-${util.formatNumber(date.getDate())} ${util.formatNumber(date.getHours())}:${util.formatNumber(date.getMinutes())}`
  },

  getScoreSummary(score) {
    if (score >= 90) return '各项指标表现优秀，请继续保持健康生活方式。'
    if (score >= 80) return '整体状态良好，建议持续关注趋势变化。'
    if (score >= 70) return '部分指标需要关注，可结合生活习惯进行改善。'
    if (score >= 60) return '健康风险提示增多，建议增加复测并咨询专业医生。'
    return '多项指标异常，请及时咨询专业医生。'
  },

  getRiskScore(level) {
    const map = { low: 25, medium: 58, high: 86 }
    return map[level] || 30
  },

  getDomainLevel(score) {
    if (score >= 82) return '良好'
    if (score >= 68) return '可观察'
    return '需关注'
  },

  formatMarkers(markers) {
    if (Array.isArray(markers)) return markers.join(' / ')
    if (typeof markers === 'string') return markers
    return ''
  },

  formatVoiceQuality(quality) {
    if (!quality || Object.keys(quality).length === 0) return []

    const duration = Number(quality.duration || 0)
    const signalQuality = Math.round(quality.signal_quality || quality.signalQuality || 0)
    const snr = Number(quality.snr_estimate || quality.snrEstimate || 0)
    const voiceRatio = Number(quality.voice_activity_ratio || quality.voiceActivityRatio || 0)
    const clipping = Number(quality.clipping_ratio || quality.clippingRatio || 0)

    return [
      {
        label: '信号质量',
        value: `${signalQuality || '--'}分`,
        desc: '环境噪声、削波和时长综合评分',
        score: signalQuality,
        color: this.getScoreColor(signalQuality)
      },
      {
        label: '录音时长',
        value: duration ? `${duration.toFixed(1)}秒` : '--',
        desc: '建议接近30秒，低于20秒稳定性会下降',
        score: duration >= 20 ? 90 : Math.max(30, Math.round(duration / 20 * 90)),
        color: this.getScoreColor(duration >= 20 ? 90 : Math.max(30, Math.round(duration / 20 * 90)))
      },
      {
        label: '信噪估计',
        value: snr ? `${snr.toFixed(1)}dB` : '--',
        desc: '数值越高，背景噪声影响越小',
        score: Math.max(0, Math.min(100, Math.round((snr / 30) * 100))),
        color: this.getScoreColor(Math.max(0, Math.min(100, Math.round((snr / 30) * 100))))
      },
      {
        label: '发声占比',
        value: voiceRatio ? `${Math.round(voiceRatio * 100)}%` : '--',
        desc: '朗读中有效声音片段占比',
        score: Math.round(voiceRatio * 100),
        color: this.getScoreColor(Math.round(voiceRatio * 100))
      },
      {
        label: '削波比例',
        value: `${(clipping * 100).toFixed(2)}%`,
        desc: '过高说明录音爆音或距离过近',
        score: Math.max(0, 100 - Math.round(clipping * 2500)),
        color: this.getScoreColor(Math.max(0, 100 - Math.round(clipping * 2500)))
      }
    ]
  },

  getScoreColor(score) {
    if (score >= 90) return '#22c55e'
    if (score >= 80) return '#3b82f6'
    if (score >= 70) return '#eab308'
    if (score >= 60) return '#f97316'
    return '#ef4444'
  },

  getRiskColor(level) {
    const map = { low: '#22c55e', medium: '#eab308', high: '#ef4444' }
    return map[level] || '#64748b'
  },

  formatVideoItem(title, icon, data) {
    if (!data) return null
    const score = Math.round(data.overall_score || data.health_score || 0)
    return {
      title,
      icon,
      score,
      color: this.getScoreColor(score),
      summary: data.summary || '分析完成'
    }
  },

  getTypeIcon(type) {
    const map = { voice: '🎤', face: '📸', video: '🎬', combined: '📊' }
    return map[type] || '🎤'
  },

  getTypeText(type) {
    const map = { voice: '语音分析', face: '面部分析', video: '视频分析', combined: '综合评估' }
    return map[type] || '语音分析'
  },

  getRiskText(level) {
    return util.getRiskText(level)
  },

  retryReport() {
    if (this.data.reportId) this.loadReport(this.data.reportId)
  },

  goBack() {
    wx.navigateBack({
      fail: () => wx.switchTab({ url: '/pages/index/index' })
    })
  },

  goHistory() {
    wx.switchTab({ url: '/pages/history/history' })
  },

  goCheckin() {
    wx.navigateTo({ url: '/pages/checkin/checkin' })
  },

  goRecheck() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  async startImprovementFromReport() {
    if (!this.data.reportId) return
    try {
      wx.showLoading({ title: '生成方案...' })
      await app.request({
        url: '/api/v1/improvement/cycles',
        method: 'POST',
        data: {
          reportId: this.data.reportId,
          days: 14
        }
      })
      wx.hideLoading()
      wx.navigateTo({ url: '/pages/improvement/improvement' })
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '生成失败', icon: 'none' })
    }
  },

  onShareAppMessage() {
    return {
      title: `VoiceHealth健康评分 ${this.data.report ? this.data.report.overallScore : '--'}分`,
      path: `/pages/report/report?id=${this.data.reportId}`
    }
  }
})
