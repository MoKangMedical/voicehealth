// pages/profile/profile.js
const app = getApp()

Page({
  data: {
    userInfo: null,
    isVip: false,
    vipExpire: '',
    loading: true,
    statsLoading: true,
    totalTests: 0,
    avgScore: 0,
    bestScore: 0,
    recentReports: [],
    menuItems: [
      { icon: '📊', title: '检测记录', url: '/pages/history/history', type: 'tab' },
      { icon: '🔬', title: '科学依据', url: '/pages/science/science', type: 'navigate' },
      { icon: '👤', title: '面部检测', url: '/pages/face/face', type: 'navigate' },
      { icon: '🎬', title: '视频检测', url: '/pages/video/video', type: 'navigate' },
      { icon: '💰', title: '价格说明', url: '', type: 'modal' },
      { icon: '📋', title: '关于我们', url: '', type: 'modal' },
      { icon: '⚙️', title: '设置', url: '', type: 'modal' }
    ]
  },

  onLoad() {
    this.updateUserStatus()
    this.loadStats()
    this.loadRecentReports()
  },

  onShow() {
    this.updateUserStatus()
    this.loadStats()
    this.loadRecentReports()
  },

  // 更新用户状态
  updateUserStatus() {
    this.setData({
      userInfo: app.globalData.userInfo,
      isVip: app.globalData.isVip,
      loading: false
    })
    // Load VIP expiry from storage
    const vipExpire = wx.getStorageSync('vipExpire')
    if (vipExpire) {
      this.setData({ vipExpire: this.formatDate(vipExpire) })
    }
  },

  // 加载统计数据
  async loadStats() {
    this.setData({ statsLoading: true })
    try {
      const res = await app.request({ url: '/api/v1/user/stats' })
      if (res) {
        const stats = res.stats || res
        this.setData({
          totalTests: stats.totalTests || stats.total_tests || stats.count || 0,
          avgScore: Math.round(stats.avgScore || stats.avg_score || stats.average || 0),
          bestScore: stats.bestScore || stats.best_score || stats.max || 0,
          statsLoading: false
        })
        // Cache stats
        wx.setStorageSync('totalTests', this.data.totalTests)
        wx.setStorageSync('avgScore', this.data.avgScore)
        wx.setStorageSync('bestScore', this.data.bestScore)
        return
      }
      this.loadStatsFromCache()
    } catch (err) {
      console.error('加载统计失败:', err)
      this.loadStatsFromCache()
    }
  },

  // 从缓存加载统计
  loadStatsFromCache() {
    this.setData({
      totalTests: wx.getStorageSync('totalTests') || 0,
      avgScore: wx.getStorageSync('avgScore') || 0,
      bestScore: wx.getStorageSync('bestScore') || 0,
      statsLoading: false
    })
  },

  // 加载最近报告
  async loadRecentReports() {
    try {
      const res = await app.request({
        url: '/api/v1/report/list?page=1&limit=3'
      })
      if (res) {
        const reports = res.reports || res.data || res.items || res.list || []
        if (Array.isArray(reports)) {
          const recentReports = reports.map(r => ({
            id: r.id || r._id || '',
            score: r.overallScore || r.score || 0,
            date: this.formatDate(r.createdAt || r.created_at || r.date),
            scoreColor: this.getScoreColor(r.overallScore || r.score || 0)
          }))
          this.setData({ recentReports })
        }
      }
    } catch (err) {
      console.error('加载最近报告失败:', err)
      // Try cache
      const cached = wx.getStorageSync('cachedRecords')
      if (cached && cached.length > 0) {
        this.setData({
          recentReports: cached.slice(0, 3).map(r => ({
            id: r.id,
            score: r.score,
            date: r.date,
            scoreColor: r.scoreColor || this.getScoreColor(r.score)
          }))
        })
      }
    }
  },

  // 格式化日期
  formatDate(dateStr) {
    if (!dateStr) return '--'
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return '--'
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  },

  // 获取评分颜色
  getScoreColor(score) {
    if (score >= 85) return '#22c55e'
    if (score >= 70) return '#3b82f6'
    if (score >= 50) return '#eab308'
    return '#ef4444'
  },

  // 获取用户头像
  onChooseAvatar(e) {
    const avatarUrl = e.detail.avatarUrl
    if (avatarUrl) {
      app.globalData.userInfo = app.globalData.userInfo || {}
      app.globalData.userInfo.avatarUrl = avatarUrl
      wx.setStorageSync('userInfo', app.globalData.userInfo)
      this.setData({ 'userInfo.avatarUrl': avatarUrl })
      // Sync to server
      this.syncProfile()
    }
  },

  // 获取用户昵称
  onNickNameInput(e) {
    const nickName = e.detail.value
    if (nickName) {
      app.globalData.userInfo = app.globalData.userInfo || {}
      app.globalData.userInfo.nickName = nickName
      wx.setStorageSync('userInfo', app.globalData.userInfo)
      this.setData({ 'userInfo.nickName': nickName })
      // Sync to server
      this.syncProfile()
    }
  },

  // 同步用户信息到服务器
  async syncProfile() {
    try {
      await app.request({
        url: '/api/v1/user/profile',
        method: 'PUT',
        data: {
          nickname: app.globalData.userInfo?.nickName || '',
          avatar_url: app.globalData.userInfo?.avatarUrl || ''
        }
      })
    } catch (err) {
      console.error('同步用户信息失败:', err)
    }
  },

  // 菜单点击
  onMenuTap(e) {
    const { url, type, title } = e.currentTarget.dataset
    if (type === 'tab') {
      wx.switchTab({ url })
    } else if (type === 'navigate') {
      wx.navigateTo({ url })
    } else if (type === 'modal') {
      this.showModal(title)
    }
  },

  // 显示弹窗
  showModal(title) {
    const content = {
      '价格说明': `单次检测: ¥${app.globalData.pricePerReport || 9.9}\nVIP月卡: ¥${app.globalData.vipPrice || 29.9} (无限次)\n每日1次免费体验`,
      '关于我们': 'VoiceHealth 基于AI声学分析技术，通过语音特征评估健康状态。仅供健康参考，不构成医学诊断。',
      '设置': '设置功能开发中...'
    }
    wx.showModal({
      title,
      content: content[title] || '功能开发中',
      showCancel: false
    })
  },

  // 开通VIP
  goVip() {
    app.showPaymentModal((success) => {
      if (success) {
        this.updateUserStatus()
        wx.showToast({ title: 'VIP开通成功', icon: 'success' })
      }
    })
  },

  // 查看报告详情
  goReport(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/report/report?id=${id}` })
    }
  },

  // 查看全部记录
  goAllRecords() {
    wx.switchTab({ url: '/pages/history/history' })
  },

  // 刷新数据
  refreshData() {
    this.loadStats()
    this.loadRecentReports()
    wx.showToast({ title: '已刷新', icon: 'success' })
  },

  onShareAppMessage() {
    return {
      title: 'VoiceHealth - AI语音健康检测',
      path: '/pages/index/index'
    }
  }
})
