// pages/face/face.js
const app = getApp()

Page({
  data: {
    cameraMode: 'front',
    photoPath: '',
    isAnalyzing: false,
    result: null,
    showResult: false
  },

  takePhoto() {
    const ctx = wx.createCameraContext()
    ctx.takePhoto({
      quality: 'high',
      success: (res) => {
        this.setData({ photoPath: res.tempImagePath })
      }
    })
  },

  choosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
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
    this.setData({ photoPath: '', result: null, showResult: false })
  },

  async analyze() {
    if (!this.data.photoPath || this.data.isAnalyzing) return
    
    this.setData({ isAnalyzing: true })
    
    try {
      wx.showLoading({ title: '分析中...' })
      
      const res = await app.uploadFile({
        url: '/api/v1/face/analyze',
        filePath: this.data.photoPath,
        name: 'image'
      })
      
      wx.hideLoading()
      
      if (res.ok) {
        const report = this.decorateReport({
          ...(res.report || {}),
          id: res.report_id,
          type: 'face',
          analysisType: 'face'
        })
        wx.setStorageSync(`report_${res.report_id}`, report)
        this.setData({
          result: report,
          showResult: true
        })
      } else {
        wx.showToast({ title: res.message || '分析失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('分析失败:', err)
      wx.showToast({ title: '分析失败', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false })
    }
  },

  getScoreColor(score) {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#3b82f6'
    if (score >= 40) return '#eab308'
    return '#ef4444'
  },

  decorateReport(report) {
    report.scoreColor = this.getScoreColor(report.overall_score || 0)
    report.dimensions = (report.dimensions || []).map(item => ({
      ...item,
      color: this.getScoreColor(item.score || 0)
    }))
    return report
  },

  onShareAppMessage() {
    return { title: 'AI面部衰老分析', path: '/pages/face/face' }
  }
})
