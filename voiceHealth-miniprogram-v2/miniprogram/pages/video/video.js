// pages/video/video.js
const app = getApp()

Page({
  data: {
    cameraMode: 'front',
    isRecording: false,
    recordingTime: 0,
    recordingTimeText: '00:00',
    timer: null,
    maxDuration: 15,
    videoPath: '',
    isAnalyzing: false,
    analyzeProgress: 0,
    result: null,
    showResult: false,
    detectItems: [
      { id: 'skin', name: '皮肤状态', icon: '🧴', enabled: true },
      { id: 'eye', name: '眼睛状态', icon: '👁️', enabled: true },
      { id: 'hair', name: '头发状态', icon: '💇', enabled: true }
    ]
  },

  switchCamera() {
    this.setData({ cameraMode: this.data.cameraMode === 'front' ? 'back' : 'front' })
  },

  toggleRecording() {
    if (this.data.isRecording) {
      this.stopRecording()
    } else {
      this.startRecording()
    }
  },

  startRecording() {
    const ctx = wx.createCameraContext()
    ctx.startRecord({
      success: () => {
        this.setData({ isRecording: true, recordingTime: 0, recordingTimeText: '00:00' })
        this.startTimer()
        setTimeout(() => { if (this.data.isRecording) this.stopRecording() }, this.data.maxDuration * 1000)
      }
    })
  },

  stopRecording() {
    const ctx = wx.createCameraContext()
    ctx.stopRecord({
      success: (res) => {
        this.stopTimer()
        this.setData({ isRecording: false, videoPath: res.tempVideoPath })
      }
    })
  },

  startTimer() {
    const timer = setInterval(() => {
      const next = this.data.recordingTime + 1
      this.setData({
        recordingTime: next,
        recordingTimeText: this.formatTime(next)
      })
    }, 1000)
    this.setData({ timer })
  },

  stopTimer() {
    if (this.data.timer) {
      clearInterval(this.data.timer)
      this.setData({ timer: null })
    }
  },

  retake() {
    this.setData({ videoPath: '', result: null, showResult: false })
  },

  toggleItem(e) {
    const id = e.currentTarget.dataset.id
    const items = this.data.detectItems.map(i => 
      i.id === id ? { ...i, enabled: !i.enabled } : i
    )
    this.setData({ detectItems: items })
  },

  async startAnalysis() {
    if (!this.data.videoPath || this.data.isAnalyzing) return
    
    this.setData({ isAnalyzing: true, analyzeProgress: 0 })
    let progressTimer = null
    
    try {
      const enabledItems = this.data.detectItems.filter(i => i.enabled).map(i => i.id)
      if (enabledItems.length === 0) {
        wx.showToast({ title: '请至少选择一项', icon: 'none' })
        this.setData({ isAnalyzing: false })
        return
      }

      progressTimer = setInterval(() => {
        if (this.data.analyzeProgress < 90) {
          this.setData({ analyzeProgress: this.data.analyzeProgress + 10 })
        }
      }, 400)

      const res = await app.uploadFile({
        url: `/api/v1/video/analyze?detect_items=${enabledItems.join(',')}`,
        filePath: this.data.videoPath,
        name: 'video'
      })

      clearInterval(progressTimer)

      if (!res.ok) {
        throw new Error(res.message || '分析失败')
      }

      const result = this.decorateResult({
        ...(res.result || {}),
        id: res.report_id,
        type: 'video',
        analysisType: 'video'
      })
      wx.setStorageSync(`report_${res.report_id}`, result)

      this.setData({
        result,
        showResult: true,
        analyzeProgress: 100
      })
    } catch (err) {
      wx.showToast({ title: err.message || '分析失败', icon: 'none' })
    } finally {
      if (progressTimer) clearInterval(progressTimer)
      this.setData({ isAnalyzing: false })
    }
  },

  formatTime(s) {
    return `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`
  },

  getScoreColor(score) {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#3b82f6'
    return '#eab308'
  },

  decorateResult(result) {
    result.scoreColor = this.getScoreColor(result.overall_score || 0)
    ;['skin', 'eye', 'hair'].forEach(key => {
      if (result[key]) {
        result[key].scoreColor = this.getScoreColor(result[key].overall_score || 0)
      }
    })
    return result
  },

  onShareAppMessage() {
    return { title: '视频健康分析结果', path: '/pages/video/video' }
  }
})
