// pages/improvement/improvement.js
// 改善闭环：问题发现 -> 方案 -> 执行 -> 复测 -> 调整

const app = getApp()

function todayStr() {
  const d = new Date()
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${day}`
}

Page({
  data: {
    loading: true,
    saving: false,
    cycle: null,
    actions: [],
    selectedActionIds: [],
    moodScore: 3,
    energyScore: 3,
    note: '',
    today: todayStr(),
    empty: false
  },

  onLoad() {
    this.loadCycle()
  },

  onPullDownRefresh() {
    this.loadCycle().finally(() => wx.stopPullDownRefresh())
  },

  async loadCycle() {
    this.setData({ loading: true, empty: false })
    try {
      const res = await app.request({ url: '/api/v1/improvement/active?autoCreate=true' })
      if (!res.cycle) {
        this.setData({ loading: false, empty: true, cycle: null, actions: [] })
        return
      }
      this.applyCycle(res.cycle)
    } catch (err) {
      this.setData({ loading: false, empty: true })
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    }
  },

  applyCycle(cycle) {
    const progress = cycle.progress || []
    const todayProgress = progress.find(item => item.checkinDate === this.data.today) || {}
    const selectedActionIds = todayProgress.completedActionIds || cycle.progressSummary.todayCompletedActionIds || []
    const selectedSet = new Set(selectedActionIds)
    const plan = cycle.plan || {}
    const actions = (plan.actions || []).map(item => ({
      ...item,
      checked: selectedSet.has(item.id),
      stepsPreview: (item.steps || []).slice(0, 2)
    }))

    this.setData({
      loading: false,
      empty: false,
      cycle,
      actions,
      selectedActionIds,
      moodScore: todayProgress.moodScore || 3,
      energyScore: todayProgress.energyScore || 3,
      note: todayProgress.note || ''
    })
  },

  onActionChange(e) {
    const selectedActionIds = e.detail.value
    const selectedSet = new Set(selectedActionIds)
    this.setData({
      selectedActionIds,
      actions: this.data.actions.map(item => ({
        ...item,
        checked: selectedSet.has(item.id)
      }))
    })
  },

  onMoodChange(e) {
    this.setData({ moodScore: Number(e.detail.value) })
  },

  onEnergyChange(e) {
    this.setData({ energyScore: Number(e.detail.value) })
  },

  onNoteInput(e) {
    this.setData({ note: e.detail.value })
  },

  async saveProgress() {
    if (!this.data.cycle || this.data.saving) return
    this.setData({ saving: true })
    try {
      const res = await app.request({
        url: `/api/v1/improvement/cycles/${this.data.cycle.id}/progress`,
        method: 'POST',
        data: {
          checkinDate: this.data.today,
          completedActionIds: this.data.selectedActionIds,
          moodScore: this.data.moodScore,
          energyScore: this.data.energyScore,
          note: this.data.note
        }
      })
      this.applyCycle(res.cycle)
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: err.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  async completeCycle() {
    if (!this.data.cycle) return
    wx.showModal({
      title: '完成本轮闭环',
      content: '完成后可根据最新报告开启下一轮改善计划。',
      confirmText: '完成',
      success: async res => {
        if (!res.confirm) return
        try {
          const result = await app.request({
            url: `/api/v1/improvement/cycles/${this.data.cycle.id}/status`,
            method: 'POST',
            data: { status: 'completed' }
          })
          this.applyCycle(result.cycle)
          wx.showToast({ title: '已完成', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: err.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  async startNewCycle() {
    try {
      wx.showLoading({ title: '生成中...' })
      const res = await app.request({
        url: '/api/v1/improvement/cycles',
        method: 'POST',
        data: { days: 14 }
      })
      wx.hideLoading()
      this.applyCycle(res.cycle)
      wx.showToast({ title: '已开启', icon: 'success' })
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '请先完成检测', icon: 'none' })
    }
  },

  goCheckin() {
    wx.navigateTo({ url: '/pages/checkin/checkin' })
  },

  goRecheck() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  goTrends() {
    wx.navigateTo({ url: '/pages/trends/trends' })
  },

  goReport() {
    const id = this.data.cycle && this.data.cycle.sourceReportId
    if (id) wx.navigateTo({ url: `/pages/report/report?id=${id}` })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth改善闭环', path: '/pages/improvement/improvement' }
  }
})
