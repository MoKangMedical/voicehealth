// pages/growth/growth.js
// VoiceHealth 商业落地、渠道推广与数字人宣传中心

const config = require('../../config.js')
const launchQueue = require('../../data/growthLaunchQueue.js')

Page({
  data: {
    metrics: [
      { value: '90天', label: '落地周期' },
      { value: '3类', label: '收入模型' },
      { value: '30条', label: '发布素材' },
      { value: '合规', label: '健康参考定位' }
    ],
    offers: [
      {
        title: '个人会员',
        price: '¥29.9/月',
        audience: '高频自测用户',
        points: ['不限次数健康参考报告', '趋势分析与改善闭环', '健康学院音频课程']
      },
      {
        title: '家庭健康包',
        price: '¥59/月',
        audience: '家庭成员共同管理',
        points: ['多成员档案', '每周健康趋势回顾', '饮食运动打卡提醒']
      },
      {
        title: '机构/API合作',
        price: '试点定制',
        audience: '体检、保险、健康管理平台',
        points: ['健康数据授权接口', '白标报告与API调用', '联合课程与私域运营']
      }
    ],
    channels: [
      {
        key: 'xhs',
        name: '小红书',
        goal: '建立真实体验与健康管理信任',
        cadence: '每周4篇笔记：体验测评2篇、知识卡片1篇、打卡复盘1篇',
        cta: '评论区引导“30秒声音健康参考”，承接到小程序/公众号私域'
      },
      {
        key: 'douyin',
        name: '抖音',
        goal: '用短视频演示30秒录音到报告的闭环',
        cadence: '每周5条短视频：场景痛点2条、产品演示2条、数字人口播1条',
        cta: '视频挂载小程序或主页组件，承接免费体验和会员转化'
      },
      {
        key: 'avatar',
        name: '数字人',
        goal: '低成本稳定输出健康学院口播和产品说明',
        cadence: '每周3条：健康误区、报告解读、改善闭环',
        cta: '片头/片尾标注AI生成，明确“仅健康管理参考”'
      }
    ],
    scripts: [
      {
        id: 'xhs-note-01',
        title: '小红书笔记：30秒声音状态自测',
        body: '我最近在试一个声音健康管理工具。不是诊断，也不是替代体检，而是用30秒朗读记录音高、停顿、能量和语速趋势。适合想观察睡眠、压力和嗓音状态变化的人。建议连续7天在同一时间录一次，看趋势比看单次分数更靠谱。'
      },
      {
        id: 'douyin-video-01',
        title: '抖音短视频：三步体验演示',
        body: '开场：你的声音，可能比你想象中更了解今天的状态。步骤一，安静环境朗读30秒。步骤二，系统提取语速、停顿、能量和音质。步骤三，查看健康参考报告和改善建议。结尾：这不是诊断，是帮你更早发现生活方式波动。'
      },
      {
        id: 'avatar-01',
        title: '数字人口播：健康参考边界',
        body: '大家好，我是VoiceHealth数字健康助手。本视频由AI数字人生成。VoiceHealth通过30秒声音记录，帮助你观察睡眠、压力、嗓音和恢复状态的趋势。结果只用于健康管理参考，不构成医学诊断；如果出现明显不适，请及时咨询专业医生。'
      }
    ],
    launchQueue,
    compliance: [
      '不写治愈率、有效率、确诊、筛查疾病等医疗化承诺',
      '不用医生、专家、患者见证作为广告推荐',
      '数字人视频显著标注AI生成或AI数字人',
      '落地页、小程序、口播都保留“健康管理参考”定位',
      '涉及用户声音、面部、视频数据时先取得授权'
    ]
  },

  copyScript(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.scripts.find(script => script.id === id)
    if (!item) return
    wx.setClipboardData({
      data: item.body,
      success: () => wx.showToast({ title: '已复制脚本', icon: 'success' })
    })
  },

  copyChannel(e) {
    const key = e.currentTarget.dataset.key
    const item = this.data.channels.find(channel => channel.key === key)
    if (!item) return
    const text = `${item.name}\n目标：${item.goal}\n节奏：${item.cadence}\n转化：${item.cta}`
    wx.setClipboardData({
      data: text,
      success: () => wx.showToast({ title: '已复制计划', icon: 'success' })
    })
  },

  copyLaunch(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.launchQueue.find(queueItem => queueItem.id === id)
    if (!item) return
    const tags = (item.tags || []).map(tag => `#${tag}`).join(' ')
    const text = `${item.day} ${item.channel} ${item.time}\n标题：${item.title}\n正文：${item.caption}\n标签：${tags}\n首评：${item.firstComment}\n转化：${item.cta}\n素材：${item.asset}\n发布前确认：健康管理参考、非诊断声明、AI生成标注`
    wx.setClipboardData({
      data: text,
      success: () => wx.showToast({ title: '已复制发布项', icon: 'success' })
    })
  },

  contactBusiness() {
    wx.setClipboardData({
      data: `${config.contact.email} / ${config.contact.wechat}`,
      success: () => wx.showToast({ title: '联系方式已复制', icon: 'success' })
    })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 商业增长中心', path: '/pages/growth/growth' }
  }
})
