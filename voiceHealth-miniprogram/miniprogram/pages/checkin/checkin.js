// pages/checkin/checkin.js
// 每日签到打卡 - 留存功能

Page({
  data: {
    isCheckedIn: false,
    streak: 0,
    totalDays: 0,
    checkinDays: [],
    weekDays: ['一', '二', '三', '四', '五', '六', '日'],
    currentWeek: [],
    rewards: [
      { days: 3, reward: '解锁AI建议', icon: '🎯', unlocked: false },
      { days: 7, reward: '7天勋章', icon: '🏅', unlocked: false },
      { days: 14, reward: '免费报告', icon: '📄', unlocked: false },
      { days: 30, reward: 'VIP体验', icon: '👑', unlocked: false }
    ]
  },

  onLoad() {
    this.loadCheckinData()
    this.generateCurrentWeek()
  },

  loadCheckinData() {
    const data = wx.getStorageSync('checkinData') || { streak: 0, totalDays: 0, days: [] }
    const today = new Date().toDateString()
    const isCheckedIn = data.days.includes(today)
    
    const rewards = this.data.rewards.map(r => ({
      ...r,
      unlocked: data.totalDays >= r.days
    }))
    
    this.setData({
      isCheckedIn,
      streak: data.streak,
      totalDays: data.totalDays,
      checkinDays: data.days,
      rewards
    })
  },

  generateCurrentWeek() {
    const now = new Date()
    const dayOfWeek = now.getDay() || 7
    const monday = new Date(now)
    monday.setDate(now.getDate() - dayOfWeek + 1)
    
    const week = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      week.push({
        date: d.getDate(),
        isToday: d.toDateString() === now.toDateString(),
        isChecked: this.data.checkinDays.includes(d.toDateString())
      })
    }
    this.setData({ currentWeek: week })
  },

  checkin() {
    if (this.data.isCheckedIn) {
      wx.showToast({ title: '今日已签到', icon: 'none' })
      return
    }
    
    const today = new Date().toDateString()
    const yesterday = new Date(Date.now() - 86400000).toDateString()
    const data = wx.getStorageSync('checkinData') || { streak: 0, totalDays: 0, days: [] }
    
    // 计算连续天数
    if (data.days.includes(yesterday)) {
      data.streak += 1
    } else {
      data.streak = 1
    }
    
    data.totalDays += 1
    data.days.push(today)
    
    wx.setStorageSync('checkinData', data)
    
    wx.showToast({ title: `签到成功！连续${data.streak}天`, icon: 'success' })
    
    this.loadCheckinData()
    this.generateCurrentWeek()
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
