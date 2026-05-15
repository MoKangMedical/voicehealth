// config.js
// VoiceHealth 配置文件

module.exports = {
  // 云环境ID。直连 FastAPI 时可留空；需要云开发能力时再填写真实环境ID。
  cloudEnv: '',
  
  // 后端API配置
  api: {
    // 生产环境API地址。上线前需要配置 HTTPS 域名，并加入小程序 request/uploadFile 合法域名。
    baseUrl: 'https://voicehealth.ai',
    // 开发环境API地址。真机调试时请改为电脑局域网IP，例如 http://192.168.1.8:8100。
    devBaseUrl: 'http://127.0.0.1:8100',
    // 是否使用开发环境（本地测试时设为true）
    useDev: true
  },

  auth: {
    // 配置后端 WECHAT_APP_ID / WECHAT_APP_SECRET 后，后端会用 wx.login code 换取 openid。
    useWechatCode: true
  },
  
  // 支付配置
  payment: {
    // 单次分析价格（单位：分）
    singlePrice: 990, // 9.9元
    // 会员月费（单位：分）
    vipMonthlyPrice: 2990, // 29.9元
    // 每天免费次数
    freePerDay: 1
  },
  
  // 分析配置
  analysis: {
    // 录音最长时间（毫秒）
    maxDuration: 60000,
    // 推荐录音时间（秒）
    recommendDuration: 30,
    // 采样率
    sampleRate: 16000,
    // 声道数
    numberOfChannels: 1,
    // 编码码率
    encodeBitRate: 96000,
    // 音频格式
    format: 'wav'
  },
  
  // 分享配置
  share: {
    title: 'VoiceHealth - AI声纹健康参考',
    path: '/pages/index/index',
    imageUrl: ''
  },
  
  // 联系方式
  contact: {
    email: 'support@voicehealth.ai',
    wechat: 'VoiceHealth_AI'
  },
  
  // 版本信息
  version: {
    current: '1.0.0',
    build: '20260427'
  }
}
