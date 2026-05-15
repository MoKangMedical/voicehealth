// pages/history/history.js
const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    records: [],
    loading: true,
    error: false,
    errorMsg: '',
    page: 1,
    limit: 20,
    hasMore: true,
    filterType: 'all',
    filters: [
      { type: 'all', text: '全部' },
      { type: 'voice', text: '语音' },
      { type: 'face', text: '面部' },
      { type: 'video', text: '视频' },
      { type: 'combined', text: '综合' }
    ]
  },

  onLoad() {
    this.loadRecords(true)
  },

  onShow() {
    this.loadRecords(true)
  },

  onPullDownRefresh() {
    this.loadRecords(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadRecords(false)
    }
  },

  async loadRecords(reset) {
    const page = reset ? 1 : this.data.page
    this.setData({ loading: true, error: false, page })

    try {
      const res = await app.request({
        url: `/api/v1/report/list?page=${page}&limit=${this.data.limit}&type=${this.data.filterType}`
      })
      const list = (res.reports || res.records || []).map(item => this.formatRecord(item))
      const records = reset ? list : this.data.records.concat(list)

      this.setData({
        records,
        loading: false,
        page: page + 1,
        hasMore: list.length >= this.data.limit,
        error: false
      })

      if (reset) wx.setStorageSync('cachedRecords', records)
    } catch (err) {
      const cached = wx.getStorageSync('cachedRecords') || []
      if (reset && cached.length > 0 && this.data.filterType === 'all') {
        this.setData({ records: cached, loading: false, error: false, hasMore: false })
        return
      }

      this.setData({
        loading: false,
        error: true,
        errorMsg: err.message || '加载记录失败'
      })
    }
  },

  formatRecord(item) {
    const type = item.analysisType || item.analysis_type || item.type || 'voice'
    const score = Math.round(item.overallScore || item.overall_score || item.score || 0)
    const createdAt = item.createdAt || item.created_at || item.date
    const level = util.getScoreLevel(score)

    return {
      id: item.id || item.reportId || '',
      type,
      typeIcon: this.getTypeIcon(type),
      typeText: this.getTypeText(type),
      score,
      scoreColor: level.color,
      scoreLevel: level.text,
      summary: item.summary || this.getScoreSummary(score),
      date: createdAt ? util.formatDate(createdAt) : '--'
    }
  },

  getScoreSummary(score) {
    if (score >= 90) return '指标优秀，继续保持'
    if (score >= 80) return '整体状态良好'
    if (score >= 70) return '部分指标需关注'
    if (score >= 60) return '建议改善生活习惯'
    return '建议咨询专业医生'
  },

  getTypeIcon(type) {
    const map = { voice: '🎤', face: '📸', video: '🎬', combined: '📊' }
    return map[type] || '🎤'
  },

  getTypeText(type) {
    const map = { voice: '语音', face: '面部', video: '视频', combined: '综合' }
    return map[type] || '语音'
  },

  switchFilter(e) {
    const type = e.currentTarget.dataset.type
    if (type === this.data.filterType) return
    this.setData({ filterType: type, records: [], page: 1, hasMore: true })
    this.loadRecords(true)
  },

  goReport(e) {
    const id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: `/pages/report/report?id=${id}` })
  },

  retryLoad() {
    this.loadRecords(true)
  },

  onShareAppMessage() {
    return { title: '我的VoiceHealth检测记录', path: '/pages/history/history' }
  }
})
