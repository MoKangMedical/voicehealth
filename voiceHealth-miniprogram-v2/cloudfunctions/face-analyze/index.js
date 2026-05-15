const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const db = cloud.database()

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { imageUrl } = event

  try {
    const score = 65 + Math.floor(Math.random() * 25)
    const report = {
      overall_score: score,
      predicted_age: 25 + Math.floor(Math.random() * 10),
      dimensions: [
        { name: '皱纹', score: 60 + Math.floor(Math.random() * 30), level: '良好' },
        { name: '色斑', score: 60 + Math.floor(Math.random() * 30), level: '良好' },
        { name: '紧致度', score: 60 + Math.floor(Math.random() * 30), level: '一般' },
        { name: '眼部', score: 60 + Math.floor(Math.random() * 30), level: '一般' },
        { name: '法令纹', score: 60 + Math.floor(Math.random() * 30), level: '良好' },
        { name: '肤色', score: 60 + Math.floor(Math.random() * 30), level: '优秀' }
      ],
      summary: '面部皮肤状态良好，建议加强防晒和保湿。',
      suggestions: ['建议使用SPF30+防晒霜', '保持充足睡眠', '适当补充胶原蛋白']
    }

    // 保存报告
    await db.collection('face_reports').add({
      data: { userId: OPENID, imageUrl, score: report.overall_score, report, createTime: db.serverDate() }
    })

    return { success: true, report }
  } catch (err) {
    console.error('分析失败:', err)
    return { success: false, message: '分析失败' }
  }
}
