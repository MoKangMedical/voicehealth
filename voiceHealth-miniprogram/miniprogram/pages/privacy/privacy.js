Page({
  data: {
    lastUpdated: '2026年4月27日'
  },
  onLoad() {},
  goBack() {
    wx.navigateBack()
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 隐私政策', path: '/pages/privacy/privacy' }
  }
})
