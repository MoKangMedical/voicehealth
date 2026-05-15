// pages/articles/articles.js
// 健康资讯 - 内容留存

Page({
  data: {
    activeTab: 0,
    tabs: ['全部', '声纹健康', '面部护理', '睡眠健康', '运动健康'],
    articles: [
      {
        id: 1,
        title: '声音中的健康密码：声纹生物标志物研究进展',
        category: '声纹健康',
        summary: '最新研究表明，人类声音中蕴含丰富的健康信息，通过AI分析可以检测多种疾病风险...',
        date: '2026-04-27',
        readTime: '5分钟',
        views: 1234,
        image: '🧬'
      },
      {
        id: 2,
        title: '面部衰老的6大维度：如何科学评估皮肤状态',
        category: '面部护理',
        summary: '面部皮肤是人体最大的器官，其衰老过程受遗传、环境、生活习惯等多因素影响...',
        date: '2026-04-26',
        readTime: '4分钟',
        views: 892,
        image: '👤'
      },
      {
        id: 3,
        title: '睡眠质量与声音特征的关系：最新研究发现',
        category: '睡眠健康',
        summary: '睡眠不足会影响声音的多个维度，包括语速、音调稳定性、停顿模式等...',
        date: '2026-04-25',
        readTime: '6分钟',
        views: 756,
        image: '😴'
      },
      {
        id: 4,
        title: '运动后的声纹变化：如何通过声音监测运动效果',
        category: '运动健康',
        summary: '运动后的声音特征会发生微妙变化，这些变化可以反映心肺功能和身体恢复状态...',
        date: '2026-04-24',
        readTime: '3分钟',
        views: 543,
        image: '🏃'
      },
      {
        id: 5,
        title: 'AI健康检测的局限性：我们应该如何看待技术边界',
        category: '声纹健康',
        summary: 'AI健康检测技术虽然发展迅速，但仍存在诸多局限性，了解这些边界有助于合理使用...',
        date: '2026-04-23',
        readTime: '7分钟',
        views: 1567,
        image: '⚠️'
      }
    ]
  },

  switchTab(e) {
    this.setData({ activeTab: parseInt(e.currentTarget.dataset.index) })
  },

  goArticle(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({ title: '文章详情开发中', icon: 'none' })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 健康资讯', path: '/pages/articles/articles' }
  }
})
