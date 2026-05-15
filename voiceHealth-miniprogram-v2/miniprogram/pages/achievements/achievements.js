// pages/achievements/achievements.js
// 成就徽章系统 - 基于后端统计和本地打卡/阅读记录

const app = getApp()

Page({
  data: {
    totalBadges: 12,
    unlockedBadges: 0,
    badges: [
      { id: 'first_check', name: '初次检测', desc: '完成第一次健康参考分析', icon: '🎯', unlocked: false },
      { id: 'voice_master', name: '声纹达人', desc: '完成5次语音分析', icon: '🎤', unlocked: false },
      { id: 'face_expert', name: '面部观察员', desc: '完成3次面部分析', icon: '📸', unlocked: false },
      { id: 'video_pioneer', name: '视频先锋', desc: '完成第一次视频分析', icon: '🎬', unlocked: false },
      { id: 'streak_3', name: '三日坚持', desc: '连续打卡3天', icon: '🔥', unlocked: false },
      { id: 'streak_7', name: '一周达人', desc: '连续打卡7天', icon: '⭐', unlocked: false },
      { id: 'streak_30', name: '月度坚持', desc: '连续打卡30天', icon: '👑', unlocked: false },
      { id: 'health_know', name: '健康学习者', desc: '阅读5篇健康知识', icon: '📚', unlocked: false },
      { id: 'share_king', name: '分享达人', desc: '分享3次健康参考', icon: '📤', unlocked: false },
      { id: 'vip_member', name: 'VIP会员', desc: '开通VIP会员', icon: '💎', unlocked: false },
      { id: 'combined_expert', name: '综合观察员', desc: '完成综合评估', icon: '🏆', unlocked: false },
      { id: 'all_rounder', name: '全能体验', desc: '使用语音、面部、视频和综合功能', icon: '🌟', unlocked: false }
    ],
    stats: {}
  },

  onLoad() {
    this.loadAchievements()
  },

  onShow() {
    this.loadAchievements()
  },

  async loadAchievements() {
    let remoteStats = {}
    try {
      const res = await app.refreshProfile()
      remoteStats = res.stats || {}
    } catch (err) {
      remoteStats = wx.getStorageSync('cachedAchievementStats') || {}
    }

    const checkinData = wx.getStorageSync('checkinData') || { streak: 0, totalDays: 0 }
    const readArticles = wx.getStorageSync('readArticles') || []
    const shareCount = wx.getStorageSync('shareCount') || 0
    const stats = {
      voiceCount: remoteStats.voice_count || 0,
      faceCount: remoteStats.face_count || 0,
      videoCount: remoteStats.video_count || 0,
      combinedCount: remoteStats.combined_count || 0,
      isVip: !!(remoteStats.is_vip || app.globalData.isVip),
      streak: checkinData.streak || 0,
      readCount: readArticles.length,
      shareCount
    }

    wx.setStorageSync('cachedAchievementStats', remoteStats)
    const badges = this.data.badges.map(badge => ({
      ...badge,
      unlocked: this.isUnlocked(badge.id, stats)
    }))
    
    const unlockedBadges = badges.filter(b => b.unlocked).length
    this.setData({ badges, unlockedBadges, stats })
  },

  isUnlocked(id, stats) {
    switch(id) {
      case 'first_check':
        return stats.voiceCount + stats.faceCount + stats.videoCount + stats.combinedCount >= 1
      case 'voice_master':
        return stats.voiceCount >= 5
      case 'face_expert':
        return stats.faceCount >= 3
      case 'video_pioneer':
        return stats.videoCount >= 1
      case 'streak_3':
        return stats.streak >= 3
      case 'streak_7':
        return stats.streak >= 7
      case 'streak_30':
        return stats.streak >= 30
      case 'health_know':
        return stats.readCount >= 5
      case 'share_king':
        return stats.shareCount >= 3
      case 'vip_member':
        return stats.isVip
      case 'combined_expert':
        return stats.combinedCount >= 1
      case 'all_rounder':
        return stats.voiceCount >= 1 && stats.faceCount >= 1 && stats.videoCount >= 1 && stats.combinedCount >= 1
      default:
        return false
    }
  },

  onShareAppMessage() {
    wx.setStorageSync('shareCount', (wx.getStorageSync('shareCount') || 0) + 1)
    return {
      title: `我已解锁${this.data.unlockedBadges}个VoiceHealth成就`,
      path: '/pages/achievements/achievements'
    }
  }
})
