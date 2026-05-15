// pages/onboarding/onboarding.js
// 引导页 - 借鉴Ada Health的简洁引导

Page({
  data: {
    currentStep: 0,
    steps: [
      {
        icon: '🎤',
        title: '声音大健康参考',
        desc: '录制接近30秒语音，分析可解释声学特征，生成25项声音健康风险提示',
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
        desc: '报告仅供个人健康管理参考，不构成医学诊断、筛查或治疗建议',
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
