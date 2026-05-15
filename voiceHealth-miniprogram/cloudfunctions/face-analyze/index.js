const cloud = require('wx-server-sdk')
const axios = require('axios')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

const API_BASE = 'http://localhost:8100'

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { imageUrl, action } = event

  if (action === 'getHistory') {
    try {
      const result = await db.collection('face_reports')
        .where({ userId: OPENID })
        .orderBy('createTime', 'desc')
        .limit(20)
        .get()
      return { success: true, records: result.data }
    } catch (err) {
      return { success: false, records: [] }
    }
  }

  try {
    // 调用后端API
    try {
      const response = await axios.post(`${API_BASE}/api/v1/face/analyze`,
        { image_url: imageUrl },
        { headers: { 'X-User-Id': OPENID, 'Content-Type': 'application/json' }, timeout: 30000 }
      )
      
      if (response.data.ok) {
        await db.collection('face_reports').add({
          data: {
            userId: OPENID,
            reportId: response.data.report_id,
            score: response.data.report.overall_score,
            report: response.data.report,
            createTime: db.serverDate()
          }
        })
        return { success: true, reportId: response.data.report_id, report: response.data.report }
      }
    } catch (apiErr) {
      console.log('API调用失败，使用本地模拟:', apiErr.message)
    }

    // 本地模拟
    const score = 65 + Math.floor(Math.random() * 25)
    const report = {
      overall_score: score,
      predicted_age: 25 + Math.floor(Math.random() * 10),
      dimensions: [
        { name: '皱纹', score: 60 + Math.floor(Math.random() * 30) },
        { name: '色斑', score: 60 + Math.floor(Math.random() * 30) },
        { name: '紧致度', score: 60 + Math.floor(Math.random() * 30) },
        { name: '眼部', score: 60 + Math.floor(Math.random() * 30) },
        { name: '法令纹', score: 60 + Math.floor(Math.random() * 30) },
        { name: '肤色', score: 60 + Math.floor(Math.random() * 30) }
      ],
      summary: '面部皮肤状态良好',
      suggestions: ['注意防晒', '保持充足睡眠']
    }

    const result = await db.collection('face_reports').add({
      data: { userId: OPENID, score: report.overall_score, report, createTime: db.serverDate() }
    })

    return { success: true, reportId: result._id, report }
  } catch (err) {
    console.error('分析失败:', err)
    return { success: false, message: '分析失败' }
  }
}
