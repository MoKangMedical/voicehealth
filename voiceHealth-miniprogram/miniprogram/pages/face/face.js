Page({
  data: {
    cameraMode: 'front',
    photoPath: '',
    isAnalyzing: false,
    result: null,
    showResult: false
  },

  onLoad() {
    // Check camera permission
    wx.authorize({
      scope: 'scope.camera',
      fail: () => {
        wx.showToast({ title: '需要相机权限', icon: 'none' })
      }
    })
  },

  onUnload() {
    // Cleanup
  },

  takePhoto() {
    const ctx = wx.createCameraContext()
    ctx.takePhoto({
      quality: 'high',
      success: res => {
        this.setData({ photoPath: res.tempImagePath })
      },
      fail: () => {
        wx.showToast({ title: '拍照失败', icon: 'none' })
      }
    })
  },

  choosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: res => {
        this.setData({ photoPath: res.tempFiles[0].tempFilePath })
      }
    })
  },

  switchCamera() {
    this.setData({
      cameraMode: this.data.cameraMode === 'front' ? 'back' : 'front'
    })
  },

  retake() {
    this.setData({
      photoPath: '',
      result: null,
      showResult: false
    })
  },

  async analyze() {
    if (!this.data.photoPath || this.data.isAnalyzing) return

    this.setData({ isAnalyzing: true })

    try {
      wx.showLoading({ title: '正在分析面部...' })

      // Simulate analysis delay
      await new Promise(r => setTimeout(r, 2500))

      // Simulated result - in production, upload photo to backend API
      const result = {
        overall_score: 72,
        predicted_age: 28,
        dimensions: [
          { name: '皱纹', score: 65, icon: '〰️', level: '良好' },
          { name: '色斑', score: 78, icon: '🔵', level: '优秀' },
          { name: '紧致度', score: 70, icon: '💪', level: '良好' },
          { name: '眼部', score: 68, icon: '👁️', level: '良好' },
          { name: '法令纹', score: 72, icon: '😊', level: '良好' },
          { name: '肤色', score: 80, icon: '🎨', level: '优秀' }
        ],
        summary: '您的面部皮肤状态良好，整体年轻度高于同龄平均水平。肤色均匀度较好，建议继续加强防晒和保湿护理。',
        suggestions: [
          '每天使用SPF30+防晒霜，预防光老化',
          '保持充足睡眠（7-8小时），促进皮肤修复',
          '使用含视黄醇的护肤品，改善细纹',
          '每周2-3次保湿面膜，提升皮肤水润度',
          '多摄入富含维C和抗氧化物质的食物'
        ]
      }

      this.setData({ result, showResult: true })
      wx.hideLoading()
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '分析失败，请重试', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false })
    }
  },

  getScoreColor(score) {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#3b82f6'
    return '#eab308'
  },

  saveResult() {
    wx.showToast({ title: '已保存', icon: 'success' })
  },

  shareResult() {
    // Share functionality
  },

  onShareAppMessage() {
    return {
      title: 'AI面部衰老分析',
      path: '/pages/face/face'
    }
  }
})
