Page({
  data: {
    lastUpdated: '2026年5月13日'
  },
  onLoad() {},
  goBack() {
    wx.navigateBack()
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 隐私政策', path: '/pages/privacy/privacy' }
  }
})
