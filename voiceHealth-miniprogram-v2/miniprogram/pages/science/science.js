// pages/science/science.js
const app = getApp()

Page({
  data: {
    activeTab: 0,
    tabs: ['理论基础', '能力范围', '参考文献', '采集指南', '打卡指南', '结果解读', '合规说明'],
    theories: [],
    papers: [],
    collectionGuide: [],
    checkinGuide: [],
    resultGuide: [],
    complianceGuide: [],
    validation: {
      accuracy: '参考',
      samples: '本地测试',
      diseases: '25',
      sensitivity: '非诊断',
      specificity: '需复测'
    },
    diseaseTotal: 0,
    diseaseGroups: []
  },

  onLoad() {
    this.loadEvidence()
    this.loadDiseases()
  },
  
  switchTab(e) {
    this.setData({ activeTab: parseInt(e.currentTarget.dataset.index) })
  },

  async loadEvidence() {
    try {
      const res = await app.rawRequest({ url: '/api/v1/evidence' })
      this.setData({
        theories: res.theories || [],
        papers: (res.references || []).map(item => ({
          ...item,
          linkText: item.doi ? `DOI: ${item.doi}` : item.url
        })),
        collectionGuide: res.collectionGuide || [],
        checkinGuide: res.checkinGuide || [],
        resultGuide: res.resultGuide || [],
        complianceGuide: res.complianceGuide || []
      })
    } catch (err) {
      console.warn('证据库加载失败:', err)
      this.setFallbackEvidence()
    }
  },

  setFallbackEvidence() {
    this.setData({
      theories: [
        { title: '声音来自呼吸-发声-共鸣-构音链路', desc: '语音可反映气息、声带振动、韵律、停顿和表达状态。', icon: '🫁' },
        { title: '结果用于趋势参考', desc: '单次结果受环境和状态影响，平台重点观察同一用户的长期变化。', icon: '📈' },
        { title: '当前不做诊断', desc: '报告仅供健康管理参考，不替代医生问诊和检查。', icon: '✅' }
      ],
      papers: [],
      collectionGuide: [
        { title: '采集要点', items: ['安静环境', '录制接近30秒', '自然语速朗读', '噪声过大时重新录制'] }
      ],
      checkinGuide: [
        { title: '每日声纹卡', desc: '固定时间、固定环境录制，重点看连续趋势。' }
      ],
      resultGuide: [
        { title: '结果解读', items: ['低关注看趋势', '中等关注建议复测', '高关注结合线下评估'] }
      ],
      complianceGuide: [
        { title: '产品定位', desc: '健康参考，不构成医学诊断、筛查或治疗建议。' }
      ]
    })
  },

  async loadDiseases() {
    try {
      const res = await app.rawRequest({ url: '/api/v1/diseases' })
      const groups = Object.keys(res.categories || {}).map(name => ({
        name,
        list: res.categories[name].map(item => ({
          ...item,
          markerText: (item.markers || []).join(' / ')
        }))
      }))
      this.setData({
        diseaseTotal: res.total || 0,
        diseaseGroups: groups,
        'validation.diseases': String(res.total || this.data.validation.diseases)
      })
    } catch (err) {
      console.warn('能力范围加载失败:', err)
    }
  },
  
  copyReference(e) {
    const url = e.currentTarget.dataset.url
    if (!url) return
    wx.setClipboardData({
      data: url,
      success: () => wx.showToast({ title: '链接已复制', icon: 'success' })
    })
  }
})
