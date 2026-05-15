// pages/family/family.js
// 家庭成员管理 - 社交功能

Page({
  data: {
    members: [
      { id: 'self', name: '我自己', relation: '本人', avatar: '👤', isMain: true }
    ],
    showAdd: false,
    newMember: { name: '', relation: '' },
    relations: ['配偶', '父亲', '母亲', '儿子', '女儿', '其他']
  },

  onLoad() {
    this.loadMembers()
  },

  loadMembers() {
    const members = wx.getStorageSync('familyMembers') || this.data.members
    this.setData({ members })
  },

  showAddMember() {
    this.setData({ showAdd: true, newMember: { name: '', relation: '' } })
  },

  hideAddMember() {
    this.setData({ showAdd: false })
  },

  inputName(e) {
    this.setData({ 'newMember.name': e.detail.value })
  },

  selectRelation(e) {
    this.setData({ 'newMember.relation': this.data.relations[e.detail.value] })
  },

  addMember() {
    if (!this.data.newMember.name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      return
    }
    
    const member = {
      id: 'member_' + Date.now(),
      name: this.data.newMember.name,
      relation: this.data.newMember.relation || '其他',
      avatar: '👤',
      isMain: false
    }
    
    const members = [...this.data.members, member]
    wx.setStorageSync('familyMembers', members)
    this.setData({ members, showAdd: false })
    wx.showToast({ title: '添加成功', icon: 'success' })
  },

  removeMember(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除该成员吗？',
      success: (res) => {
        if (res.confirm) {
          const members = this.data.members.filter(m => m.id !== id)
          wx.setStorageSync('familyMembers', members)
          this.setData({ members })
        }
      }
    })
  },

  selectMember(e) {
    const id = e.currentTarget.dataset.id
    wx.setStorageSync('activeFamilyMemberId', id)
    wx.showToast({ title: '已选择成员', icon: 'success' })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 家庭健康管理', path: '/pages/family/family' }
  }
})
