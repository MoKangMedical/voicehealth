// pages/articles/articles.js
// 健康知识库 - 内容留存与用户教育

Page({
  data: {
    activeTab: 0,
    tabs: ['全部', '声音健康', '采集复测', '睡眠压力', '隐私合规'],
    articles: [
      {
        id: 'voice-biomarker',
        title: '声音里的健康线索：能看什么，不能看什么',
        category: '声音健康',
        summary: '声音可反映呼吸、嗓音、韵律、疲劳和压力线索，但单次结果不能作为疾病诊断。',
        date: '2026-05-13',
        readTime: '4分钟',
        image: '🎤',
        content: 'VoiceHealth会分析音高、停顿、语速、能量、音质和频谱等可解释特征。请把结果当作健康管理参考，重点观察连续趋势。若出现胸痛、明显气促、突然说话不清等症状，应优先就医。'
      },
      {
        id: 'collection-protocol',
        title: '30秒录音怎么做更稳定',
        category: '采集复测',
        summary: '环境、距离、时长和朗读方式会直接影响声音特征。固定条件复测比单次分数更重要。',
        date: '2026-05-13',
        readTime: '3分钟',
        image: '📏',
        content: '建议在安静室内录制，手机麦克风距口部约15-25厘米。使用自然语速朗读固定文本，录制接近30秒。剧烈运动、饮酒、感冒发热或长时间用嗓后不建议立即采集。'
      },
      {
        id: 'baseline-trend',
        title: '建立个人声音基线',
        category: '采集复测',
        summary: '连续7天在相似环境下采集，可形成更可靠的个人趋势参考。',
        date: '2026-05-13',
        readTime: '3分钟',
        image: '📈',
        content: '建议先连续7天在相近时间、相近环境录制。日常管理每周2-3次即可。若同一维度连续3次明显下降，再结合睡眠、压力、运动和症状判断是否需要线下评估。'
      },
      {
        id: 'sleep-stress',
        title: '睡眠、压力与声音状态',
        category: '睡眠压力',
        summary: '疲劳、焦虑和压力可能影响语速、停顿、能量和韵律。',
        date: '2026-05-13',
        readTime: '4分钟',
        image: '😴',
        content: '睡眠不足和压力升高可能让声音变慢、停顿增多、韵律变平或能量下降。记录睡眠时长、咖啡因、主观压力和运动恢复，有助于解释趋势变化。'
      },
      {
        id: 'voice-care',
        title: '嗓音保护与饮食水分卡',
        category: '声音健康',
        summary: '饮水、咖啡因、酒精、辛辣油腻和睡前进食，都可能影响咽喉和嗓音状态。',
        date: '2026-05-13',
        readTime: '3分钟',
        image: '💧',
        content: '咽喉干涩、气声升高或嘶哑时，优先补水、减少烟酒和刺激性饮食，避免睡前进食。持续嘶哑超过两周，或伴随吞咽困难、咽喉疼痛，应咨询耳鼻喉医生。'
      },
      {
        id: 'privacy-boundary',
        title: '健康数据和隐私边界',
        category: '隐私合规',
        summary: '语音、面部、视频和健康推断都属于敏感场景，使用前应理解授权和删除路径。',
        date: '2026-05-13',
        readTime: '5分钟',
        image: '🔒',
        content: '平台应最小化采集数据，仅用于生成报告、趋势和账号服务。您可以查看隐私政策并请求删除账号、报告和本地缓存。任何健康参考都不应替代医生问诊和检查。'
      }
    ],
    filteredArticles: []
  },

  onLoad() {
    this.applyFilter()
  },

  switchTab(e) {
    this.setData({ activeTab: parseInt(e.currentTarget.dataset.index) }, () => this.applyFilter())
  },

  applyFilter() {
    const tab = this.data.tabs[this.data.activeTab]
    const filteredArticles = tab === '全部'
      ? this.data.articles
      : this.data.articles.filter(item => item.category === tab)
    this.setData({ filteredArticles })
  },

  goArticle(e) {
    const id = e.currentTarget.dataset.id
    const article = this.data.articles.find(item => item.id === id)
    if (!article) return

    const readArticles = wx.getStorageSync('readArticles') || []
    if (!readArticles.includes(id)) {
      readArticles.push(id)
      wx.setStorageSync('readArticles', readArticles)
    }

    wx.showModal({
      title: article.title,
      content: article.content,
      showCancel: false,
      confirmText: '知道了'
    })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 健康知识库', path: '/pages/articles/articles' }
  }
})
