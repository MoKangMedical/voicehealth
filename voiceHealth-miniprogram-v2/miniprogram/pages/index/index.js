// pages/index/index.js
const app = getApp()
const util = require('../../utils/util.js')
const config = require('../../config.js')
const recorderManager = wx.getRecorderManager()

function formatDateForApi(date) {
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

Page({
  data: {
    isRecording: false,
    recordingTime: 0,
    recordingTimeText: '00:00',
    timer: null,
    canAnalyze: false,
    audioFilePath: '',
    isAnalyzing: false,
    freeCount: 0,
    maxFree: 1,
    isVip: false,
    readingText: null,
    showReadingText: false,
    dashboard: {
      latestScore: '--',
      latestLabel: '暂无报告',
      latestReportId: '',
      checkinText: '待打卡',
      cycleText: '未开启',
      freeText: '今日1次',
      hasReport: false,
      hasCheckin: false,
      hasCycle: false
    },
    tips: [
      '请在安静环境下录制',
      '请朗读下方显示的文字',
      '保持正常语速和音量',
      '录制接近30秒更利于趋势参考'
    ]
  },

  onLoad() {
    this.setData({
      userInfo: app.globalData.userInfo,
      freeCount: app.globalData.freeCount,
      maxFree: app.globalData.maxFreePerDay,
      isVip: app.globalData.isVip
    })
    this.fetchReadingText()
    this.loadMobileDashboard()
  },

  onShow() {
    app.refreshProfile().catch(() => {})
    this.setData({
      userInfo: app.globalData.userInfo,
      freeCount: app.globalData.freeCount,
      isVip: app.globalData.isVip
    })
    this.loadMobileDashboard()
  },

  async loadMobileDashboard() {
    try {
      const res = await app.request({ url: '/api/v1/health-data/summary' })
      const latestReports = res.latestReports || []
      const latest = latestReports[0] || null
      const lifestyle = res.lifestyle || {}
      const latestCheckin = lifestyle.latest || null
      const today = formatDateForApi(new Date())
      const activeCycle = res.improvement && res.improvement.activeCycle
      const progress = activeCycle && activeCycle.progressSummary
      const summary = res.summary || {}

      this.setData({
        dashboard: {
          latestScore: latest ? Math.round(latest.score || 0) : '--',
          latestLabel: latest ? latest.typeName || '最近报告' : '暂无报告',
          latestReportId: latest ? latest.id || '' : '',
          checkinText: latestCheckin && latestCheckin.checkinDate === today ? '今日已打卡' : '待打卡',
          cycleText: activeCycle ? `${progress ? progress.completionRate || 0 : 0}%` : '未开启',
          freeText: summary.isVip ? '会员可用' : `剩余${summary.freeRemaining || 0}次`,
          hasReport: !!latest,
          hasCheckin: !!(latestCheckin && latestCheckin.checkinDate === today),
          hasCycle: !!activeCycle
        }
      })
    } catch (err) {
      this.setData({
        'dashboard.freeText': this.data.isVip ? '会员可用' : `已用${this.data.freeCount}/${this.data.maxFree}`
      })
    }
  },

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
          text: '春天来了，花儿开了，小鸟在枝头唱歌。阳光温暖地照在大地上，万物复苏，生机勃勃。',
          keywords: ['春天', '花儿', '小鸟', '阳光']
        },
        showReadingText: true
      })
    }
  },

  refreshReadingText() {
    this.fetchReadingText()
    wx.showToast({ title: '已刷新', icon: 'success' })
  },

  toggleRecording() {
    if (this.data.isRecording) {
      this.stopRecording()
    } else {
      this.startRecording()
    }
  },

  startRecording() {
    if (!app.globalData.userInfo) {
      this.getUserProfile()
      return
    }

    recorderManager.start({
      duration: config.analysis.maxDuration,
      sampleRate: config.analysis.sampleRate,
      numberOfChannels: config.analysis.numberOfChannels,
      encodeBitRate: config.analysis.encodeBitRate,
      format: config.analysis.format
    })

    recorderManager.onStart(() => {
      this.setData({ isRecording: true, recordingTime: 0, recordingTimeText: '00:00' })
      this.startTimer()
    })

    recorderManager.onError((err) => {
      console.error('录音失败:', err)
      wx.showToast({ title: '录音失败，请重试', icon: 'none' })
    })
  },

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

  startTimer() {
    const timer = setInterval(() => {
      const next = this.data.recordingTime + 1
      this.setData({
        recordingTime: next,
        recordingTimeText: util.formatDuration(next)
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

  getUserProfile() {
    wx.getUserProfile({
      desc: '用于生成健康参考报告',
      success: (res) => {
        const userInfo = res.userInfo
        app.globalData.userInfo = userInfo
        wx.setStorageSync('userInfo', userInfo)
        this.setData({ userInfo })
        app.ensureUser(true)
          .then(() => this.startRecording())
          .catch(() => wx.showToast({ title: '登录失败，请重试', icon: 'none' }))
      },
      fail: () => {
        wx.showToast({ title: '需要授权才能使用', icon: 'none' })
      }
    })
  },

  async startAnalysis() {
    if (!this.data.canAnalyze || this.data.isAnalyzing) return

    if (!app.globalData.isVip && !app.canUseFree()) {
      this.showPaymentModal()
      return
    }

    this.setData({ isAnalyzing: true })

    try {
      wx.showLoading({ title: '分析中...' })

      const readingTextId = (this.data.readingText && this.data.readingText.id) || 'standard_1'
      const res = await app.uploadFile({
        url: `/api/v1/voice/analyze?reading_text_id=${readingTextId}`,
        filePath: this.data.audioFilePath,
        name: 'audio'
      })

      wx.hideLoading()

      if (res.ok) {
        if (!app.globalData.isVip && app.canUseFree()) {
          app.useFree()
          this.setData({ freeCount: app.globalData.freeCount })
        }

        const reportId = res.report_id
        wx.setStorageSync(`report_${reportId}`, {
          ...(res.report || {}),
          id: reportId,
          analysisType: 'voice',
          type: 'voice'
        })
        app.refreshProfile().catch(() => {})
        wx.navigateTo({ url: `/pages/report/report?id=${reportId}` })
      } else {
        wx.showToast({ title: res.message || '分析失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('分析失败:', err)
      wx.showToast({ title: '网络错误，请重试', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false, canAnalyze: false, recordingTime: 0, recordingTimeText: '00:00' })
    }
  },

  showPaymentModal() {
    app.showPaymentModal((success) => {
      if (success) this.startAnalysis()
    })
  },

  formatTime(seconds) {
    return util.formatDuration(seconds)
  },

  goScience() {
    wx.navigateTo({ url: '/pages/science/science' })
  },

  goFace() {
    wx.navigateTo({ url: '/pages/face/face' })
  },

  goCombined() {
    wx.navigateTo({ url: '/pages/combined/combined' })
  },

  goVideo() {
    wx.navigateTo({ url: '/pages/video/video' })
  },

  goTrends() {
    wx.navigateTo({ url: '/pages/trends/trends' })
  },

  openLatestReport() {
    if (this.data.dashboard.latestReportId) {
      wx.navigateTo({ url: `/pages/report/report?id=${this.data.dashboard.latestReportId}` })
      return
    }
    wx.switchTab({ url: '/pages/history/history' })
  },

  goOrders() {
    wx.navigateTo({ url: '/pages/orders/orders' })
  },

  goCheckin() {
    wx.navigateTo({ url: '/pages/checkin/checkin' })
  },

  goImprovement() {
    wx.navigateTo({ url: '/pages/improvement/improvement' })
  },

  goPlans() {
    wx.navigateTo({ url: '/pages/plans/plans' })
  },

  goArticles() {
    wx.navigateTo({ url: '/pages/articles/articles' })
  },

  goAchievements() {
    wx.navigateTo({ url: '/pages/achievements/achievements' })
  },

  goFamily() {
    wx.navigateTo({ url: '/pages/family/family' })
  },

  goPrivacy() {
    wx.navigateTo({ url: '/pages/privacy/privacy' })
  },

  goOnboarding() {
    wx.navigateTo({ url: '/pages/onboarding/onboarding' })
  }
})
