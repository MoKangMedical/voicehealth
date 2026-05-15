// pages/trends/trends.js
// 健康趋势图表 - 借鉴Apple Health

Page({
  data: {
    activeRange: 'week',
    ranges: ['week', 'month', '3month', 'year'],
    rangeLabels: ['7天', '30天', '3个月', '1年'],
    chartData: [],
    stats: {
      avgScore: 0,
      maxScore: 0,
      minScore: 0,
      trend: 0
    },
    insights: []
  },

  onLoad() {
    this.generateMockData()
  },

  generateMockData() {
    const days = this.data.activeRange === 'week' ? 7 : 
                 this.data.activeRange === 'month' ? 30 :
                 this.data.activeRange === '3month' ? 90 : 365
    
    const data = []
    let base = 70
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      base += (Math.random() - 0.45) * 5
      base = Math.max(50, Math.min(95, base))
      data.push({
        date: `${d.getMonth()+1}/${d.getDate()}`,
        score: Math.round(base),
        type: ['voice', 'face', 'video'][Math.floor(Math.random() * 3)]
      })
    }
    
    const scores = data.map(d => d.score)
    const avg = Math.round(scores.reduce((a,b) => a+b, 0) / scores.length)
    const max = Math.max(...scores)
    const min = Math.min(...scores)
    const trend = scores[scores.length-1] - scores[0]
    
    const insights = []
    if (trend > 5) insights.push('📈 您的健康评分呈上升趋势，继续保持！')
    else if (trend < -5) insights.push('📉 健康评分有所下降，建议增加检测频率')
    else insights.push('📊 您的健康状态保持稳定')
    
    if (avg >= 80) insights.push('💪 平均评分优秀，状态良好')
    else if (avg >= 60) insights.push('👍 平均评分良好，还有提升空间')
    else insights.push('⚠️ 平均评分偏低，建议关注健康')
    
    this.setData({
      chartData: data,
      stats: { avgScore: avg, maxScore: max, minScore: min, trend },
      insights
    })
  },

  switchRange(e) {
    this.setData({ activeRange: e.currentTarget.dataset.range })
    this.generateMockData()
  },

  getScoreColor(score) {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#3b82f6'
    return '#eab308'
  },

  onShareAppMessage() {
    return { title: '我的健康趋势', path: '/pages/trends/trends' }
  }
})
