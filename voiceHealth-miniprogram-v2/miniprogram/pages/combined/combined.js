// pages/combined/combined.js
const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    loadingSources: true,
    isAnalyzing: false,
    showResult: false,
    combinedResult: null,
    sourceMap: {},
    sources: [
      { type: 'voice', icon: '🎤', name: '声纹数据', status: '未采集', active: false },
      { type: 'face', icon: '📸', name: '面部数据', status: '未采集', active: false },
      { type: 'video', icon: '🎬', name: '视频数据', status: '未采集', active: false }
    ]
  },

  onLoad() {
    this.loadSources()
  },

  onShow() {
    this.loadSources()
  },

  async loadSources() {
    this.setData({ loadingSources: true })
    try {
      const res = await app.request({ url: '/api/v1/report/list?page=1&limit=50&type=all' })
      const reports = res.reports || res.records || []
      const sourceMap = {}

      reports.forEach(report => {
        const type = report.analysisType || report.type
        if (!sourceMap[type] && ['voice', 'face', 'video'].includes(type)) {
          sourceMap[type] = report
        }
      })

      const sources = this.data.sources.map(item => {
        const report = sourceMap[item.type]
        return {
          ...item,
          active: !!report,
          score: report ? Math.round(report.overallScore || report.overall_score || report.score || 0) : '--',
          status: report ? `${util.formatDate(report.createdAt || report.created_at)} · ${Math.round(report.overallScore || report.overall_score || report.score || 0)}分` : '未采集'
        }
      })

      this.setData({ sourceMap, sources, loadingSources: false })
    } catch (err) {
      this.setData({ loadingSources: false })
      wx.showToast({ title: '数据源加载失败', icon: 'none' })
    }
  },

  async startCombinedAnalysis() {
    if (this.data.isAnalyzing) return

    const sourceMap = this.data.sourceMap || {}
    const sourceCount = ['voice', 'face', 'video'].filter(type => sourceMap[type]).length
    if (sourceCount === 0) {
      wx.showModal({
        title: '缺少检测数据',
        content: '请先完成语音、面部或视频检测，再生成综合评估。',
        confirmText: '去检测',
        success: res => {
          if (res.confirm) wx.switchTab({ url: '/pages/index/index' })
        }
      })
      return
    }

    this.setData({ isAnalyzing: true })

    try {
      wx.showLoading({ title: '综合分析中...' })
      const res = await app.request({
        url: '/api/v1/combined/analyze',
        method: 'POST',
        data: {
          voice_report_id: sourceMap.voice && sourceMap.voice.id,
          face_report_id: sourceMap.face && sourceMap.face.id,
          video_report_id: sourceMap.video && sourceMap.video.id
        }
      })

      wx.hideLoading()

      if (!res.ok || !res.report) throw new Error('综合评估失败')

      const report = this.decorateReport(res.report)
      wx.setStorageSync(`report_${res.report_id}`, report)
      this.setData({
        combinedResult: report,
        showResult: true
      })
      app.refreshProfile().catch(() => {})
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '分析失败', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false })
    }
  },

  decorateReport(report) {
    const score = Math.round(report.overallScore || report.overall_score || report.score || 0)
    return {
      ...report,
      id: report.id || report.report_id,
      overall_score: score,
      biological_age: report.biologicalAge || report.biological_age || report.predictedAge || '--',
      scoreColor: this.getScoreColor(score),
      dimensions: (report.dimensions || []).map(item => ({
        ...item,
        color: this.getScoreColor(item.score || 0)
      })),
      suggestions: report.suggestions || (report.aiAdvice || []).map(item => item.content).filter(Boolean)
    }
  },

  getScoreColor(score) {
    if (score >= 90) return '#22c55e'
    if (score >= 80) return '#3b82f6'
    if (score >= 70) return '#eab308'
    if (score >= 60) return '#f97316'
    return '#ef4444'
  },

  goReport() {
    const id = this.data.combinedResult && this.data.combinedResult.id
    if (id) wx.navigateTo({ url: `/pages/report/report?id=${id}` })
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  goVoice() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  goFace() {
    wx.navigateTo({ url: '/pages/face/face' })
  },

  goVideo() {
    wx.navigateTo({ url: '/pages/video/video' })
  },

  onShareAppMessage() {
    return { title: '我的综合健康评估结果', path: '/pages/combined/combined' }
  }
})
