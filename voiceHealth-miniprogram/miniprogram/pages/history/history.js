// pages/history/history.js
const app = getApp()
const { formatTime, getRiskColor, getRiskText } = require('../../utils/util.js')

Page({
  data: {
    records: [],
    loading: true,
    error: false,
    errorMsg: '',
    refreshing: false,
    page: 1,
    hasMore: true,
    filterType: 'all' // all, voice, face, video
  },

  onLoad() {
    this.loadRecords()
  },

  onShow() {
    // Refresh on show to pick up new records
    this.setData({ page: 1, hasMore: true })
    this.loadRecords()
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.setData({ refreshing: true, page: 1, hasMore: true })
    this.loadRecords().then(() => {
      wx.stopPullDownRefresh()
      this.setData({ refreshing: false })
    })
  },

  // 上拉加载
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 })
      this.loadMore()
    }
  },

  // 加载记录
  async loadRecords() {
    this.setData({ loading: true, error: false })
    try {
      const res = await app.request({
        url: `/api/v1/report/list?page=${this.data.page}&limit=20`
      })
      if (res) {
        const reports = res.reports || res.data || res.items || res.list || []
        if (Array.isArray(reports)) {
          const records = reports.map(r => this.formatRecord(r))
          this.setData({
            records: this.data.page === 1 ? records : [...this.data.records, ...records],
            loading: false,
            hasMore: reports.length >= 20
          })
          // Cache records locally
          if (this.data.page === 1) {
            wx.setStorageSync('cachedRecords', records)
          }
          return
        }
      }
      // If API returns no valid data, try cache
      this.loadFromCache()
    } catch (err) {
      console.error('加载记录失败:', err)
      // Try loading from cache
      this.loadFromCache()
    }
  },

  // 从缓存加载
  loadFromCache() {
    const cached = wx.getStorageSync('cachedRecords')
    if (cached && cached.length > 0) {
      this.setData({
        records: cached,
        loading: false,
        error: false
      })
      wx.showToast({ title: '已加载缓存数据', icon: 'none', duration: 1500 })
    } else {
      this.setData({
        loading: false,
        error: true,
        errorMsg: '暂无检测记录'
      })
    }
  },

  // 加载更多
  async loadMore() {
    try {
      const res = await app.request({
        url: `/api/v1/report/list?page=${this.data.page}&limit=20`
      })
      if (res) {
        const reports = res.reports || res.data || res.items || res.list || []
        if (Array.isArray(reports) && reports.length > 0) {
          const newRecords = reports.map(r => this.formatRecord(r))
          this.setData({
            records: [...this.data.records, ...newRecords],
            hasMore: reports.length >= 20
          })
        } else {
          this.setData({ hasMore: false })
        }
      } else {
        this.setData({ hasMore: false })
      }
    } catch (err) {
      console.error('加载更多失败:', err)
      this.setData({ hasMore: false })
    }
  },

  // 格式化记录
  formatRecord(r) {
    const score = r.overallScore || r.score || r.totalScore || 0
    const type = r.analysisType || r.analysis_type || r.type || 'voice'
    return {
      id: r.id || r._id || r.reportId || '',
      score: score,
      date: this.formatDate(r.createdAt || r.created_at || r.date),
      summary: r.summary || r.desc || this.getScoreSummary(score),
      type: type,
      typeIcon: this.getTypeIcon(type),
      typeText: this.getTypeText(type),
      scoreColor: this.getScoreColor(score)
    }
  },

  // 格式化日期
  formatDate(dateStr) {
    if (!dateStr) return '--'
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return '--'
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  },

  // 获取评分总结
  getScoreSummary(score) {
    if (score >= 85) return '各项指标优秀，继续保持'
    if (score >= 70) return '整体健康状态良好'
    if (score >= 50) return '部分指标需关注'
    return '建议及时改善生活习惯'
  },

  // 获取评分颜色
  getScoreColor(score) {
    if (score >= 85) return '#22c55e'
    if (score >= 70) return '#3b82f6'
    if (score >= 50) return '#eab308'
    return '#ef4444'
  },

  // 获取类型图标
  getTypeIcon(type) {
    const iconMap = { voice: '🎤', face: '📸', video: '🎬', combined: '📊' }
    return iconMap[type] || '🎤'
  },

  // 获取类型文本
  getTypeText(type) {
    const textMap = { voice: '语音', face: '面部', video: '视频', combined: '综合' }
    return textMap[type] || '语音'
  },

  // 切换筛选类型
  switchFilter(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ filterType: type })
  },

  // 删除记录
  deleteRecord(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条检测记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await app.request({
              url: `/api/v1/report/${id}`,
              method: 'DELETE'
            })
            // Remove from local list
            const records = this.data.records.filter(r => r.id !== id)
            this.setData({ records })
            wx.showToast({ title: '已删除', icon: 'success' })
          } catch (err) {
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 跳转到报告
  goReport(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/report/report?id=${id}` })
    }
  },

  // 重试加载
  retryLoad() {
    this.setData({ page: 1, hasMore: true })
    this.loadRecords()
  },

  onShareAppMessage() {
    return { title: '我的健康检测记录', path: '/pages/history/history' }
  }
})
