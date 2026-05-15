const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  console.log('payment-callback', event)
  
  // 模拟分析结果
  const score = 65 + Math.floor(Math.random() * 25)
  
  return {
    success: true,
    reportId: `mock_${Date.now()}`,
    report: {
      overall_score: score,
      summary: '分析完成，状态良好',
      features: [
        { name: '指标1', score: 80 },
        { name: '指标2', score: 75 },
        { name: '指标3', score: 70 }
      ],
      suggestions: ['保持良好作息', '适当运动']
    }
  }
}
