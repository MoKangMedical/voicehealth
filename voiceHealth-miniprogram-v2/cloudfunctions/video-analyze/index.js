const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const db = cloud.database()

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { videoBase64, detectItems } = event

  try {
    const items = detectItems || ['skin', 'eye', 'hair']
    const result = {
      overall_score: 65 + Math.floor(Math.random() * 25),
      biological_age: 25 + Math.floor(Math.random() * 10),
      timestamp: new Date().toISOString()
    }

    if (items.includes('skin')) {
      result.skin = {
        overall_score: 60 + Math.floor(Math.random() * 30),
        summary: '肤色均匀，轻微痘痘',
        acne_level: 'mild',
        wrinkle_level: 'none',
        suggestions: ['注意防晒', '保持清洁']
      }
    }

    if (items.includes('eye')) {
      result.eye = {
        overall_score: 60 + Math.floor(Math.random() * 30),
        summary: '轻微黑眼圈',
        dark_circle_level: 'mild',
        fatigue_level: 'none',
        suggestions: ['保证充足睡眠']
      }
    }

    if (items.includes('hair')) {
      result.hair = {
        overall_score: 60 + Math.floor(Math.random() * 30),
        summary: '发量正常，发质良好',
        density_level: 'normal',
        gray_level: 'none',
        suggestions: ['保持健康饮食']
      }
    }

    // 保存报告
    await db.collection('video_reports').add({
      data: { userId: OPENID, result, detectItems: items, createTime: db.serverDate() }
    })

    return { success: true, result }
  } catch (err) {
    console.error('分析失败:', err)
    return { success: false, message: '分析失败' }
  }
}
