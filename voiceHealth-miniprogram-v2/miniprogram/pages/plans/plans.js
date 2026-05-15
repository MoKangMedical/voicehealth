// pages/plans/plans.js
const app = getApp()

Page({
  data: {
    loading: true,
    domains: [],
    activeDomain: 'all',
    plans: [],
    allPlans: []
  },

  onLoad() {
    this.loadPlans()
  },

  onPullDownRefresh() {
    this.loadPlans().finally(() => wx.stopPullDownRefresh())
  },

  async loadPlans() {
    this.setData({ loading: true })
    try {
      const res = await app.request({ url: '/api/v1/health-plans' })
      this.setData({
        loading: false,
        domains: res.domains || ['all'],
        allPlans: res.plans || [],
        plans: res.plans || []
      })
    } catch (err) {
      this.setData({ loading: false })
      wx.showToast({ title: '方案加载失败', icon: 'none' })
    }
  },

  switchDomain(e) {
    const domain = e.currentTarget.dataset.domain
    const plans = domain === 'all'
      ? this.data.allPlans
      : this.data.allPlans.filter(item => item.domain === domain)
    this.setData({ activeDomain: domain, plans })
  },

  showPlan(e) {
    const id = e.currentTarget.dataset.id
    const plan = this.data.allPlans.find(item => item.id === id)
    if (!plan) return

    const content = [
      plan.summary,
      '',
      `目标：${plan.target}`,
      '',
      '执行步骤：',
      ...(plan.steps || []).map((step, index) => `${index + 1}. ${step}`),
      '',
      `注意：${(plan.cautions || []).join(' ')}`,
      '',
      `来源：${(plan.sources || []).map(item => item.name).join('；')}`
    ].join('\n')

    wx.showModal({
      title: plan.title,
      content,
      showCancel: false,
      confirmText: '知道了'
    })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth循证健康方案库', path: '/pages/plans/plans' }
  }
})
