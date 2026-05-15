// pages/combined/combined.js
// 综合健康评估 - 声纹+面部双维度

Page({
  data: {
    hasVoice: false,
    hasFace: false,
    voiceResult: null,
    faceResult: null,
    combinedResult: null,
    isAnalyzing: false,
    showResult: false,
    dimensions: [
      { name: '心血管', icon: '❤️', score: 0 },
      { name: '呼吸系统', icon: '🫁', score: 0 },
      { name: '神经系统', icon: '🧠', score: 0 },
      { name: '内分泌', icon: '⚖️', score: 0 },
      { name: '免疫系统', icon: '🛡️', score: 0 },
      { name: '衰老程度', icon: '⏳', score: 0 }
    ]
  },

  onLoad(options) {
    // 从URL参数获取声纹和面部数据
    if (options.voice) {
      try {
        this.setData({
          hasVoice: true,
          voiceResult: JSON.parse(decodeURIComponent(options.voice))
        })
      } catch (e) { console.error('解析声纹数据失败:', e) }
    }
    if (options.face) {
      try {
        this.setData({
          hasFace: true,
          faceResult: JSON.parse(decodeURIComponent(options.face))
        })
      } catch (e) { console.error('解析面部数据失败:', e) }
    }
  },

  async startCombinedAnalysis() {
    if (this.data.isAnalyzing) return
    this.setData({ isAnalyzing: true })
    
    try {
      wx.showLoading({ title: '综合分析中...' })
      
      // 模拟多维度分析
      await new Promise(r => setTimeout(r, 2500))
      
      const dimensions = [
        { name: '心血管', icon: '❤️', score: 65 + Math.floor(Math.random() * 25) },
        { name: '呼吸系统', icon: '🫁', score: 65 + Math.floor(Math.random() * 25) },
        { name: '神经系统', icon: '🧠', score: 65 + Math.floor(Math.random() * 25) },
        { name: '内分泌', icon: '⚖️', score: 65 + Math.floor(Math.random() * 25) },
        { name: '免疫系统', icon: '🛡️', score: 65 + Math.floor(Math.random() * 25) },
        { name: '衰老程度', icon: '⏳', score: 65 + Math.floor(Math.random() * 25) }
      ]
      
      const overallScore = Math.floor(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length)
      const bioAge = 25 + Math.floor(Math.random() * 10)
      
      wx.hideLoading()
      
      this.setData({
        combinedResult: {
          overall_score: overallScore,
          biological_age: bioAge,
          dimensions: dimensions,
          summary: `综合评估显示您的整体健康状态${overallScore >= 75 ? '良好' : overallScore >= 60 ? '一般' : '需要关注'}。生物学年龄${bioAge}岁，各项指标均在可控范围内。`,
          suggestions: [
            '保持规律作息，每天睡眠7-8小时',
            '每周进行3-4次中等强度运动',
            '均衡饮食，多摄入蔬果和优质蛋白',
            '定期进行健康体检，关注异常指标'
          ]
        },
        showResult: true
      })
    } catch (err) {
      wx.hideLoading()
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

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  onShareAppMessage() {
    const score = this.data.combinedResult?.overall_score || 0
    return {
      title: `我的综合健康评估：${score}分`,
      path: '/pages/combined/combined'
    }
  }
})
