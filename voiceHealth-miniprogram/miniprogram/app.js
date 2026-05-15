// miniprogram/app.js
// VoiceHealth 小程序入口

const config = require('./config.js')

App({
  onLaunch() {
    // 初始化云开发
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上基础库')
      return
    }
    
    wx.cloud.init({
      env: config.cloudEnv,
      traceUser: true
    })

    // 获取用户信息
    // 检查是否已看过引导页
    const hasOnboarded = wx.getStorageSync('hasOnboarded')
    if (!hasOnboarded) {
      wx.redirectTo({ url: '/pages/onboarding/onboarding' })
    }
    
    this.globalData.userInfo = wx.getStorageSync('userInfo') || null
    this.globalData.userId = wx.getStorageSync('userId') || null
    this.globalData.freeCount = wx.getStorageSync('freeCount') || 0
    this.globalData.isVip = wx.getStorageSync('isVip') || false

    // 自动登录
    this.autoLogin()
  },

  globalData: {
    userInfo: null,
    userId: null,
    freeCount: 0,
    isVip: false,
    maxFreePerDay: 1,
    pricePerReport: 9.9,
    vipPrice: 29.9
  },

  // 自动登录
  async autoLogin() {
    if (this.globalData.userId) {
      // 已有用户ID，检查VIP状态
      this.checkVipStatus()
      return
    }

    // 获取openid
    try {
      const res = await wx.cloud.callFunction({ name: 'getOpenid' })
      if (res.result.openid) {
        this.globalData.openid = res.result.openid
        
        // 注册/登录
        const loginRes = await this.request({
          url: '/api/v1/user/register',
          method: 'POST',
          data: {
            openid: res.result.openid,
            nickname: this.globalData.userInfo?.nickName || '',
            avatar_url: this.globalData.userInfo?.avatarUrl || ''
          }
        })

        if (loginRes.ok) {
          this.globalData.userId = loginRes.user.id
          this.globalData.isVip = loginRes.is_vip
          wx.setStorageSync('userId', loginRes.user.id)
          wx.setStorageSync('isVip', loginRes.is_vip)
        }
      }
    } catch (err) {
      console.error('自动登录失败:', err)
    }
  },

  // 检查VIP状态
  checkVipStatus() {
    const vipExpire = wx.getStorageSync('vipExpire')
    if (vipExpire && new Date(vipExpire) > new Date()) {
      this.globalData.isVip = true
    } else {
      this.globalData.isVip = false
      wx.setStorageSync('isVip', false)
    }
  },

  // 检查免费次数
  canUseFree() {
    const today = new Date().toDateString()
    const lastDate = wx.getStorageSync('lastFreeDate')
    
    if (lastDate !== today) {
      this.globalData.freeCount = 0
      wx.setStorageSync('freeCount', 0)
      wx.setStorageSync('lastFreeDate', today)
    }
    
    return this.globalData.freeCount < this.globalData.maxFreePerDay
  },

  // 使用免费次数
  useFree() {
    this.globalData.freeCount++
    wx.setStorageSync('freeCount', this.globalData.freeCount)
    wx.setStorageSync('lastFreeDate', new Date().toDateString())
  },

  // 获取API基础URL
  getApiBaseUrl() {
    return config.api.useDev ? config.api.devBaseUrl : config.api.baseUrl
  },

  // 通用请求方法
  request(options) {
    const baseUrl = this.getApiBaseUrl()
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
          'X-User-Id': this.globalData.userId || '',
          ...options.header
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else if (res.statusCode === 403) {
            // 免费次数用完
            reject({ code: 403, message: res.data?.detail || '免费次数已用完' })
          } else {
            reject({ code: res.statusCode, message: res.data?.detail || '请求失败' })
          }
        },
        fail: (err) => {
          reject({ code: -1, message: err.errMsg || '网络错误' })
        }
      })
    })
  },

  // 显示支付弹窗
  showPaymentModal(callback) {
    wx.showModal({
      title: '免费次数已用完',
      content: `今日免费次数已用完。单次分析${this.globalData.pricePerReport}元，或开通VIP会员${this.globalData.vipPrice}元/月无限次使用。`,
      confirmText: '开通VIP',
      cancelText: '单次购买',
      success: (res) => {
        if (res.confirm) {
          this.createOrder('vip_monthly', this.globalData.vipPrice * 100, callback)
        } else if (res.cancel) {
          this.createOrder('single', this.globalData.pricePerReport * 100, callback)
        }
      }
    })
  },

  // 创建订单
  async createOrder(type, amount, callback) {
    try {
      wx.showLoading({ title: '创建订单...' })
      
      const res = await this.request({
        url: '/api/v1/order/create',
        method: 'POST',
        data: { type, amount }
      })

      wx.hideLoading()

      if (res.ok) {
        // 调起支付
        wx.requestPayment({
          ...res.payment,
          success: () => {
            wx.showToast({ title: '支付成功', icon: 'success' })
            if (type === 'vip_monthly') {
              this.globalData.isVip = true
              wx.setStorageSync('isVip', true)
            }
            callback && callback(true)
          },
          fail: () => {
            wx.showToast({ title: '支付取消', icon: 'none' })
            callback && callback(false)
          }
        })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '创建订单失败', icon: 'none' })
      callback && callback(false)
    }
  }
})
