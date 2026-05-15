const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const db = cloud.database()

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { action, audioPath, reportId } = event

  switch (action) {
    case 'getReport':
      return await getReport(reportId)
    case 'getHistory':
      return await getHistory(OPENID)
    default:
      return await analyzeAudio(OPENID, audioPath)
  }
}

async function analyzeAudio(userId, audioPath) {
  try {
    // 上传音频
    const audioResult = await cloud.uploadFile({
      fileContent: Buffer.from(audioPath, 'base64'),
      cloudPath: `audio/${userId}/${Date.now()}.wav`
    })

    // 生成模拟报告
    const score = 65 + Math.floor(Math.random() * 25)
    const report = {
      overall_score: score,
      summary: '您的声纹特征显示整体健康状态良好',
      features: [
        { name: '语速', value: '4.2字/秒', percent: 85 },
        { name: '音调', value: '180Hz', percent: 72 },
        { name: '音量', value: '65dB', percent: 68 },
        { name: '清晰度', value: '92%', percent: 92 },
        { name: '稳定性', value: '88%', percent: 88 },
        { name: '停顿', value: '正常', percent: 75 }
      ],
      risks: [
        { name: '心血管', level: 'low', levelText: '低风险', suggestion: '保持规律运动' },
        { name: '呼吸系统', level: 'low', levelText: '低风险', suggestion: '注意空气质量' },
        { name: '神经系统', level: 'low', levelText: '低风险', suggestion: '保证充足睡眠' }
      ],
      insight: '基于声纹分析，建议保持良好作息习惯。'
    }

    // 保存报告
    const result = await db.collection('reports').add({
      data: {
        userId,
        audioFileId: audioResult.fileID,
        score: report.overall_score,
        report,
        createTime: db.serverDate()
      }
    })

    return {
      success: true,
      reportId: result._id,
      report
    }
  } catch (err) {
    console.error('分析失败:', err)
    return { success: false, message: '分析失败' }
  }
}

async function getReport(reportId) {
  try {
    const result = await db.collection('reports').doc(reportId).get()
    return { success: true, report: result.data.report }
  } catch (err) {
    return { success: false, message: '报告不存在' }
  }
}

async function getHistory(userId) {
  try {
    const result = await db.collection('reports')
      .where({ userId })
      .orderBy('createTime', 'desc')
      .limit(20)
      .get()
    return { success: true, records: result.data }
  } catch (err) {
    return { success: false, records: [] }
  }
}
