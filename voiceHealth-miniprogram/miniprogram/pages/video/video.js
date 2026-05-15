// pages/video/video.js
// 视频健康分析 - 皮肤/眼睛/头发检测

Page({
  data: {
    cameraMode: 'front',
    isRecording: false,
    recordingTime: 0,
    timer: null,
    maxDuration: 15,
    videoPath: '',
    isAnalyzing: false,
    analyzeProgress: 0,
    result: null,
    showResult: false,
    detectItems: [
      { id: 'skin', name: '皮肤状态', icon: '🧴', desc: '肤色/痘痘/皱纹', enabled: true },
      { id: 'eye', name: '眼睛状态', icon: '👁️', desc: '黑眼圈/眼袋/疲劳', enabled: true },
      { id: 'hair', name: '头发状态', icon: '💇', desc: '发量/发质/白发', enabled: true }
    ]
  },

  onUnload() {
    this.stopTimer()
  },

  switchCamera() {
    this.setData({
      cameraMode: this.data.cameraMode === 'front' ? 'back' : 'front'
    })
  },

  startRecording() {
    const ctx = wx.createCameraContext()
    ctx.startRecord({
      success: () => {
        this.setData({ isRecording: true, recordingTime: 0 })
        this.startTimer()
        // 自动停止
        setTimeout(() => {
          if (this.data.isRecording) this.stopRecording()
        }, this.data.maxDuration * 1000)
      },
      fail: (err) => {
        console.error('录制失败:', err)
        wx.showToast({ title: '录制失败', icon: 'none' })
      }
    })
  },

  stopRecording() {
    const ctx = wx.createCameraContext()
    ctx.stopRecord({
      success: (res) => {
        this.stopTimer()
        this.setData({
          isRecording: false,
          videoPath: res.tempVideoPath
        })
      },
      fail: (err) => {
        console.error('停止录制失败:', err)
        this.stopTimer()
        this.setData({ isRecording: false })
      }
    })
  },

  startTimer() {
    const timer = setInterval(() => {
      this.setData({ recordingTime: this.data.recordingTime + 1 })
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
    this.setData({
      videoPath: '',
      result: null,
      showResult: false,
      analyzeProgress: 0
    })
  },

  toggleItem(e) {
    const id = e.currentTarget.dataset.id
    const items = this.data.detectItems.map(item =>
      item.id === id ? { ...item, enabled: !item.enabled } : item
    )
    this.setData({ detectItems: items })
  },

  async startAnalysis() {
    if (!this.data.videoPath || this.data.isAnalyzing) return
    
    const enabledItems = this.data.detectItems.filter(i => i.enabled)
    if (enabledItems.length === 0) {
      wx.showToast({ title: '请选择检测项目', icon: 'none' })
      return
    }

    this.setData({ isAnalyzing: true, analyzeProgress: 0 })

    try {
      // 模拟分析进度
      for (let i = 0; i <= 90; i += 15) {
        await new Promise(r => setTimeout(r, 400))
        this.setData({ analyzeProgress: i })
      }

      // 生成分析结果
      const result = {
        overall_score: 65 + Math.floor(Math.random() * 25),
        biological_age: 25 + Math.floor(Math.random() * 10),
        skin: enabledItems.find(i => i.id === 'skin') ? {
          overall_score: 60 + Math.floor(Math.random() * 30),
          summary: '肤色均匀，轻微痘痘，建议注意防晒',
          suggestions: ['使用SPF30+防晒霜', '保持面部清洁']
        } : null,
        eye: enabledItems.find(i => i.id === 'eye') ? {
          overall_score: 60 + Math.floor(Math.random() * 30),
          summary: '轻微黑眼圈，建议保证充足睡眠',
          suggestions: ['每晚睡眠7-8小时', '减少屏幕使用时间']
        } : null,
        hair: enabledItems.find(i => i.id === 'hair') ? {
          overall_score: 60 + Math.floor(Math.random() * 30),
          summary: '发量正常，发质良好',
          suggestions: ['均衡饮食', '避免频繁烫染']
        } : null
      }

      this.setData({
        result: result,
        showResult: true,
        analyzeProgress: 100
      })
    } catch (err) {
      console.error('分析失败:', err)
      wx.showToast({ title: '分析失败', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false })
    }
  },

  formatTime(seconds) {
    const min = Math.floor(seconds / 60)
    const sec = seconds % 60
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  },

  getScoreColor(score) {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#3b82f6'
    if (score >= 40) return '#eab308'
    return '#ef4444'
  },

  onShareAppMessage() {
    const score = this.data.result?.overall_score || 0
    return {
      title: `视频健康分析结果：${score}分`,
      path: '/pages/video/video'
    }
  }
})
