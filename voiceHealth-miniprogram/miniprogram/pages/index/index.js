// pages/index/index.js
// 首页 - 完整的语音检测流程

const app = getApp()
const config = require('../../config.js')
const recorderManager = wx.getRecorderManager()

Page({
  data: {
    // 用户状态
    userInfo: null,
    isVip: false,
    freeCount: 0,
    maxFree: 1,
    
    // 录音状态
    isRecording: false,
    recordingTime: 0,
    timer: null,
    canAnalyze: false,
    audioFilePath: '',
    
    // 分析状态
    isAnalyzing: false,
    analyzeStep: '',
    
    // 朗读文本
    readingText: null,
    showReadingText: false,
    
    // 提示
    tips: [
      '请在安静环境下录制',
      '请朗读下方显示的文字',
      '保持正常语速和音量',
      '录制30秒效果最佳'
    ]
  },

  onLoad() {
    this.updateUserStatus()
    this.fetchReadingText()
  },

  onShow() {
    this.updateUserStatus()
  },

  // 更新用户状态
  updateUserStatus() {
    this.setData({
      userInfo: app.globalData.userInfo,
      isVip: app.globalData.isVip,
      freeCount: app.globalData.freeCount,
      maxFree: app.globalData.maxFreePerDay
    })
  },

  // 获取朗读文本
  async fetchReadingText() {
    try {
      const res = await app.request({ url: '/api/v1/verification/text' })
      if (res.ok) {
        this.setData({ readingText: res.text, showReadingText: true })
      }
    } catch (err) {
      console.error('获取朗读文本失败:', err)
      this.setData({
        readingText: {
          id: 'standard_1',
          text: '春天来了，花儿开了，小鸟在枝头唱歌。阳光温暖地照在大地上，万物复苏，生机勃勃。我喜欢在这样的日子里，和朋友们一起去公园散步，感受大自然的美好。',
          keywords: ['春天', '花儿', '小鸟', '阳光']
        },
        showReadingText: true
      })
    }
  },

  // 刷新朗读文本
  refreshReadingText() {
    this.fetchReadingText()
    wx.showToast({ title: '已刷新', icon: 'success' })
  },

  // 开始录音
  startRecording() {
    // 检查登录状态
    if (!app.globalData.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }

    // 检查权限
    if (!app.globalData.isVip && !app.canUseFree()) {
      app.showPaymentModal((success) => {
        if (success) {
          this.updateUserStatus()
          this.startRecording()
        }
      })
      return
    }

    // 开始录音
    recorderManager.start({
      duration: config.analysis.maxDuration,
      sampleRate: config.analysis.sampleRate,
      numberOfChannels: config.analysis.numberOfChannels,
      encodeBitRate: config.analysis.encodeBitRate,
      format: config.analysis.format
    })

    recorderManager.onStart(() => {
      this.setData({ isRecording: true, recordingTime: 0 })
      this.startTimer()
    })

    recorderManager.onError((err) => {
      console.error('录音失败:', err)
      wx.showToast({ title: '录音失败，请重试', icon: 'none' })
    })
  },

  // 停止录音
  stopRecording() {
    recorderManager.stop()
    recorderManager.onStop((res) => {
      this.stopTimer()
      this.setData({
        isRecording: false,
        audioFilePath: res.tempFilePath,
        canAnalyze: true
      })
    })
  },

  // 开始计时
  startTimer() {
    const timer = setInterval(() => {
      this.setData({ recordingTime: this.data.recordingTime + 1 })
    }, 1000)
    this.setData({ timer })
  },

  // 停止计时
  stopTimer() {
    if (this.data.timer) {
      clearInterval(this.data.timer)
      this.setData({ timer: null })
    }
  },

  // 开始分析
  async startAnalysis() {
    if (!this.data.canAnalyze || this.data.isAnalyzing) return

    this.setData({ 
      isAnalyzing: true,
      analyzeStep: '准备中...'
    })

    try {
      // 读取音频文件
      this.setData({ analyzeStep: '上传音频...' })
      const fileManager = wx.getFileSystemManager()
      const audioBase64 = fileManager.readFileSync(this.data.audioFilePath, 'base64')

      // 调用云函数分析
      this.setData({ analyzeStep: '分析中...' })
      const res = await wx.cloud.callFunction({
        name: 'analyze',
        data: {
          audioPath: audioBase64,
          readingTextId: this.data.readingText?.id
        }
      })

      if (res.result.success) {
        // 使用免费次数
        if (!app.globalData.isVip) {
          app.useFree()
          this.setData({ freeCount: app.globalData.freeCount })
        }

        // 跳转到报告页
        this.setData({ analyzeStep: '生成报告...' })
        wx.navigateTo({
          url: `/pages/report/report?id=${res.result.reportId}`
        })
      } else {
        wx.showToast({ title: res.result.message || '分析失败', icon: 'none' })
      }
    } catch (err) {
      console.error('分析失败:', err)
      wx.showToast({ title: '网络错误，请重试', icon: 'none' })
    } finally {
      this.setData({ 
        isAnalyzing: false,
        canAnalyze: false,
        recordingTime: 0,
        analyzeStep: ''
      })
    }
  },

  // 格式化时间
  formatTime(seconds) {
    const min = Math.floor(seconds / 60)
    const sec = seconds % 60
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  },

  // 页面跳转
  goScience() { wx.navigateTo({ url: '/pages/science/science' }) },
  goFace() { wx.navigateTo({ url: '/pages/face/face' }) },
  goCombined() { wx.navigateTo({ url: '/pages/combined/combined' }) },
  goVideo() { wx.navigateTo({ url: '/pages/video/video' }) },

  // 分享功能
  goCheckin(){wx.navigateTo({url:"/pages/checkin/checkin"})},
  goArticles(){wx.navigateTo({url:"/pages/articles/articles"})},
  goPrivacy(){wx.navigateTo({url:"/pages/privacy/privacy"})},
  onShareAppMessage() {
    return {
      title: 'VoiceHealth - AI声纹健康检测',
      path: '/pages/index/index'
    }
  }
})
