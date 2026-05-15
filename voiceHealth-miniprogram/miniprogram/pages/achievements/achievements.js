// pages/achievements/achievements.js
// 成就徽章系统 - 游戏化

Page({
  data: {
    totalBadges: 12,
    unlockedBadges: 0,
    badges: [
      { id: 'first_check', name: '初次检测', desc: '完成第一次健康检测', icon: '🎯', unlocked: false, requirement: 1 },
      { id: 'voice_master', name: '声纹达人', desc: '完成5次语音检测', icon: '🎤', unlocked: false, requirement: 5 },
      { id: 'face_expert', name: '面部专家', desc: '完成3次面部分析', icon: '📸', unlocked: false, requirement: 3 },
      { id: 'video_pioneer', name: '视频先锋', desc: '完成第一次视频分析', icon: '🎬', unlocked: false, requirement: 1 },
      { id: 'streak_3', name: '三日坚持', desc: '连续签到3天', icon: '🔥', unlocked: false, requirement: 3 },
      { id: 'streak_7', name: '一周达人', desc: '连续签到7天', icon: '⭐', unlocked: false, requirement: 7 },
      { id: 'streak_30', name: '月度冠军', desc: '连续签到30天', icon: '👑', unlocked: false, requirement: 30 },
      { id: 'health_know', name: '健康达人', desc: '阅读10篇健康资讯', icon: '📚', unlocked: false, requirement: 10 },
      { id: 'share_king', name: '分享达人', desc: '分享5次检测结果', icon: '📤', unlocked: false, requirement: 5 },
      { id: 'vip_member', name: 'VIP会员', desc: '开通VIP会员', icon: '💎', unlocked: false, requirement: 1 },
      { id: 'combined_expert', name: '综合专家', desc: '完成综合评估', icon: '🏆', unlocked: false, requirement: 1 },
      { id: 'all_rounder', name: '全能选手', desc: '使用所有检测功能', icon: '🌟', unlocked: false, requirement: 4 }
    ]
  },

  onLoad() {
    this.loadAchievements()
  },

  loadAchievements() {
    const stats = wx.getStorageSync('userStats') || {}
    const badges = this.data.badges.map(badge => {
      let unlocked = false
      switch(badge.id) {
        case 'first_check': unlocked = (stats.voiceCount || 0) >= 1; break
        case 'voice_master': unlocked = (stats.voiceCount || 0) >= 5; break
        case 'face_expert': unlocked = (stats.faceCount || 0) >= 3; break
        case 'video_pioneer': unlocked = (stats.videoCount || 0) >= 1; break
        case 'streak_3': unlocked = (stats.streak || 0) >= 3; break
        case 'streak_7': unlocked = (stats.streak || 0) >= 7; break
        case 'streak_30': unlocked = (stats.streak || 0) >= 30; break
        case 'vip_member': unlocked = stats.isVip || false; break
        case 'combined_expert': unlocked = (stats.combinedCount || 0) >= 1; break
        case 'all_rounder': unlocked = (stats.voiceCount||0)>=1 && (stats.faceCount||0)>=1 && (stats.videoCount||0)>=1 && (stats.combinedCount||0)>=1; break
        default: unlocked = false
      }
      return { ...badge, unlocked }
    })
    
    const unlockedBadges = badges.filter(b => b.unlocked).length
    this.setData({ badges, unlockedBadges })
  },

  onShareAppMessage() {
    return {
      title: `我已解锁${this.data.unlockedBadges}个成就徽章！`,
      path: '/pages/achievements/achievements'
    }
  }
})
