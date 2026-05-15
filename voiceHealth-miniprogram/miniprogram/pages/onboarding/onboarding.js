// pages/onboarding/onboarding.js
// 引导页 - 借鉴Ada Health的简洁引导

Page({
  data: {
    currentStep: 0,
    steps: [
      {
        icon: '🎤',
        title: 'AI声纹检测',
        desc: '录制30秒语音，AI分析59维声学特征，评估25种疾病风险',
        color: '#3b82f6'
      },
      {
        icon: '📸',
        title: '面部衰老分析',
        desc: 'AI识别6大面部维度，预测生物年龄，提供改善建议',
        color: '#22c55e'
      },
      {
        icon: '🎬',
        title: '视频健康检测',
        desc: '一键检测皮肤、眼睛、头发状态，全面了解健康状况',
        color: '#eab308'
      },
      {
        icon: '🔒',
        title: '隐私安全',
        desc: '数据加密存储，仅供个人健康参考，不构成医学诊断',
        color: '#8b5cf6'
      }
    ]
  },

  nextStep() {
    if (this.data.currentStep < this.data.steps.length - 1) {
      this.setData({ currentStep: this.data.currentStep + 1 })
    } else {
      this.goHome()
    }
  },

  skip() {
    this.goHome()
  },

  goHome() {
    wx.setStorageSync('hasOnboarded', true)
    wx.switchTab({ url: '/pages/index/index' })
  }
})
