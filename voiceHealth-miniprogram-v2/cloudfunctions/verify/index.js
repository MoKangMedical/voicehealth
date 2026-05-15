const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { audioBase64, expectedTextId } = event

  // 模拟验证结果（80%通过率）
  const passed = Math.random() > 0.2

  return {
    is_valid: passed,
    liveness: {
      is_live: passed,
      confidence: passed ? 0.85 : 0.45,
      score: passed ? 0.82 : 0.38,
      reason: passed ? '' : '可能不是真人发声'
    },
    reading: {
      is_valid: passed,
      confidence: passed ? 0.78 : 0.35,
      match_ratio: passed ? 0.75 : 0.25,
      reason: passed ? '' : '朗读内容不匹配'
    }
  }
}
