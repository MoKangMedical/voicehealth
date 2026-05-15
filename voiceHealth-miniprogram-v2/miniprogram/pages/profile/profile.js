// pages/profile/profile.js
const app = getApp()
const config = require('../../config.js')

Page({
  data: {
    userInfo: null,
    user: null,
    isVip: false,
    vipExpire: '',
    loading: true,
    stats: {
      total_reports: 0,
      voice_count: 0,
      face_count: 0,
      video_count: 0,
      combined_count: 0,
      avg_score: 0,
      best_score: 0,
      free_remaining: 0
    },
    menuItems: [
      { icon: '📋', title: '检测记录', url: '/pages/history/history', type: 'tab' },
      { icon: '🔬', title: '科学依据', url: '/pages/science/science', type: 'navigate' },
      { icon: '📸', title: '面部分析', url: '/pages/face/face', type: 'navigate' },
      { icon: '🎬', title: '视频分析', url: '/pages/video/video', type: 'navigate' },
      { icon: '📊', title: '综合评估', url: '/pages/combined/combined', type: 'navigate' },
      { icon: '📈', title: '趋势分析', url: '/pages/trends/trends', type: 'navigate' },
      { icon: '🔁', title: '改善闭环', url: '/pages/improvement/improvement', type: 'navigate' },
      { icon: '📌', title: '循证健康方案', url: '/pages/plans/plans', type: 'navigate' },
      { icon: '📅', title: '每日健康打卡', url: '/pages/checkin/checkin', type: 'navigate' },
      { icon: '📚', title: '健康知识库', url: '/pages/articles/articles', type: 'navigate' },
      { icon: '🏅', title: '成就徽章', url: '/pages/achievements/achievements', type: 'navigate' },
      { icon: '👨‍👩‍👧', title: '家庭成员', url: '/pages/family/family', type: 'navigate' },
      { icon: '🧾', title: '订单记录', url: '/pages/orders/orders', type: 'navigate' },
      { icon: '🔒', title: '隐私政策', url: '/pages/privacy/privacy', type: 'navigate' },
      { icon: '🧭', title: '新手引导', url: '/pages/onboarding/onboarding', type: 'navigate' },
      { icon: '💳', title: '会员与价格', url: '', type: 'pricing' },
      { icon: 'ℹ️', title: '关于VoiceHealth', url: '', type: 'about' }
    ]
  },

  onLoad() {
    this.syncLocalState()
    this.loadProfile()
  },

  onShow() {
    this.syncLocalState()
    this.loadProfile()
  },

  syncLocalState() {
    this.setData({
      userInfo: app.globalData.userInfo,
      user: app.globalData.user,
      isVip: app.globalData.isVip,
      vipExpire: this.formatDate(wx.getStorageSync('vipExpire'))
    })
  },

  async loadProfile() {
    this.setData({ loading: true })
    try {
      const res = await app.refreshProfile()
      this.setData({
        user: res.user,
        stats: res.stats || this.data.stats,
        isVip: !!res.is_vip,
        vipExpire: this.formatDate((res.user && res.user.vip_expire_at) || ''),
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  login() {
    wx.getUserProfile({
      desc: '用于展示个人健康档案',
      success: res => {
        app.globalData.userInfo = res.userInfo
        wx.setStorageSync('userInfo', res.userInfo)
        this.setData({ userInfo: res.userInfo })
        app.ensureUser(true)
          .then(() => this.loadProfile())
          .catch(() => wx.showToast({ title: '登录失败', icon: 'none' }))
      }
    })
  },

  onChooseAvatar(e) {
    const avatarUrl = e.detail.avatarUrl
    app.globalData.userInfo = app.globalData.userInfo || {}
    app.globalData.userInfo.avatarUrl = avatarUrl
    wx.setStorageSync('userInfo', app.globalData.userInfo)
    this.setData({ 'userInfo.avatarUrl': avatarUrl })
    this.syncProfile()
  },

  onNickNameInput(e) {
    const nickName = e.detail.value
    app.globalData.userInfo = app.globalData.userInfo || {}
    app.globalData.userInfo.nickName = nickName
    wx.setStorageSync('userInfo', app.globalData.userInfo)
    this.setData({ 'userInfo.nickName': nickName })
    this.syncProfile()
  },

  async syncProfile() {
    try {
      await app.ensureUser()
      await app.request({
        url: '/api/v1/user/profile',
        method: 'PUT',
        data: {
          nickname: (app.globalData.userInfo && app.globalData.userInfo.nickName) || '',
          avatar_url: (app.globalData.userInfo && app.globalData.userInfo.avatarUrl) || ''
        }
      })
      this.loadProfile()
    } catch (err) {
      wx.showToast({ title: '资料同步失败', icon: 'none' })
    }
  },

  onMenuTap(e) {
    const item = e.currentTarget.dataset
    if (item.type === 'tab') {
      wx.switchTab({ url: item.url })
    } else if (item.type === 'navigate') {
      wx.navigateTo({ url: item.url })
    } else if (item.type === 'pricing') {
      this.showPricing()
    } else if (item.type === 'about') {
      this.showAbout()
    }
  },

  showPricing() {
    wx.showModal({
      title: '会员与价格',
      content: `每日免费 ${config.payment.freePerDay} 次\n月度会员 ¥${config.payment.vipMonthlyPrice / 100}\n单次参考报告 ¥${config.payment.singlePrice / 100}`,
      showCancel: false
    })
  },

  showAbout() {
    wx.showModal({
      title: '关于VoiceHealth',
      content: 'VoiceHealth 通过语音、面部和视频生物标志物生成健康参考报告。报告不构成医学诊断，如有不适请咨询专业医生。',
      showCancel: false
    })
  },

  goVip() {
    app.showPaymentModal(success => {
      if (success) this.loadProfile()
    })
  },

  formatDate(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return ''
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth - AI语音健康参考', path: '/pages/index/index' }
  }
})
