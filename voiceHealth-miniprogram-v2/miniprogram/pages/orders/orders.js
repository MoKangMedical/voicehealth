// pages/orders/orders.js
const app = getApp()
const config = require('../../config.js')
const util = require('../../utils/util.js')

Page({
  data: {
    loading: true,
    error: false,
    orders: []
  },

  onLoad() {
    this.loadOrders()
  },

  onShow() {
    this.loadOrders()
  },

  onPullDownRefresh() {
    this.loadOrders().finally(() => wx.stopPullDownRefresh())
  },

  async loadOrders() {
    this.setData({ loading: true, error: false })
    try {
      const res = await app.request({ url: '/api/v1/order/list?limit=50' })
      const orders = (res.orders || []).map(order => this.formatOrder(order))
      this.setData({ orders, loading: false })
    } catch (err) {
      this.setData({ loading: false, error: true })
      wx.showToast({ title: '订单加载失败', icon: 'none' })
    }
  },

  formatOrder(order) {
    return {
      ...order,
      typeText: this.getTypeText(order.type),
      statusText: this.getStatusText(order.status),
      statusClass: order.status || 'pending',
      amountText: `¥${((order.amount || 0) / 100).toFixed(2)}`,
      dateText: util.formatDate(order.created_at)
    }
  },

  getTypeText(type) {
    const map = {
      single: '单次报告',
      vip_monthly: '月度会员',
      vip_yearly: '年度会员'
    }
    return map[type] || '订单'
  },

  getStatusText(status) {
    const map = {
      pending: '待支付',
      paid: '已支付',
      refunded: '已退款',
      cancelled: '已取消'
    }
    return map[status] || '处理中'
  },

  buyVip() {
    app.showPaymentModal(success => {
      if (success) this.loadOrders()
    })
  },

  showPricing() {
    wx.showModal({
      title: '会员与价格',
      content: `每日免费 ${config.payment.freePerDay} 次\n月度会员 ¥${config.payment.vipMonthlyPrice / 100}\n单次参考报告 ¥${config.payment.singlePrice / 100}`,
      showCancel: false
    })
  },

  retryLoad() {
    this.loadOrders()
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth会员服务', path: '/pages/orders/orders' }
  }
})
