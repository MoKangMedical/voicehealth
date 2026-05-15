// app.js
const config = require('./config.js')

const CLIENT_ID_KEY = 'vhClientId'
const USER_KEY = 'vhUser'

function createClientId() {
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

App({
  onLaunch: function () {
    if (wx.cloud && config.cloudEnv && config.cloudEnv !== 'voicehealth-xxxxx') {
      wx.cloud.init({
        env: config.cloudEnv,
        traceUser: true,
      })
    }

    const clientId = wx.getStorageSync(CLIENT_ID_KEY) || createClientId()
    wx.setStorageSync(CLIENT_ID_KEY, clientId)

    this.globalData.clientId = clientId
    this.globalData.user = wx.getStorageSync(USER_KEY) || null
    this.globalData.userInfo = wx.getStorageSync('userInfo') || null
    this.globalData.freeCount = wx.getStorageSync('freeCount') || 0
    this.globalData.isVip = wx.getStorageSync('isVip') || false
    this.globalData.maxFreePerDay = config.payment.freePerDay
    this.checkVipStatus()
    this.ensureUser().catch(err => console.warn('用户初始化失败:', err))
  },

  globalData: {
    user: null,
    userInfo: null,
    clientId: '',
    freeCount: 0,
    isVip: false,
    maxFreePerDay: 1,
    pricePerReport: 9.9,
    vipPrice: 29.9
  },

  getApiBaseUrl: function () {
    return config.api.useDev ? config.api.devBaseUrl : config.api.baseUrl
  },

  checkVipStatus: function () {
    const vipExpire = wx.getStorageSync('vipExpire')
    if (vipExpire && new Date(vipExpire) > new Date()) {
      this.globalData.isVip = true
      wx.setStorageSync('isVip', true)
    } else if (vipExpire) {
      this.globalData.isVip = false
      wx.setStorageSync('isVip', false)
    }
  },

  canUseFree: function () {
    const today = new Date().toDateString()
    const lastDate = wx.getStorageSync('lastFreeDate')
    if (lastDate !== today) {
      this.globalData.freeCount = 0
      wx.setStorageSync('freeCount', 0)
      wx.setStorageSync('lastFreeDate', today)
    }
    return this.globalData.freeCount < this.globalData.maxFreePerDay
  },

  useFree: function () {
    this.globalData.freeCount += 1
    wx.setStorageSync('freeCount', this.globalData.freeCount)
    wx.setStorageSync('lastFreeDate', new Date().toDateString())
  },

  syncSession: function (payload) {
    if (!payload) return

    if (payload.user) {
      this.globalData.user = payload.user
      wx.setStorageSync(USER_KEY, payload.user)
      if (payload.user.vip_expire_at) {
        wx.setStorageSync('vipExpire', payload.user.vip_expire_at)
      }
    }

    if (payload.stats) {
      this.globalData.freeCount = payload.stats.free_count || 0
      this.globalData.isVip = !!payload.stats.is_vip || !!payload.is_vip
      wx.setStorageSync('freeCount', this.globalData.freeCount)
      wx.setStorageSync('isVip', this.globalData.isVip)
      if (payload.stats.vip_expire_at) {
        wx.setStorageSync('vipExpire', payload.stats.vip_expire_at)
      }
    } else if (payload.is_vip !== undefined) {
      this.globalData.isVip = !!payload.is_vip
      wx.setStorageSync('isVip', this.globalData.isVip)
    }
  },

  ensureUser: function (force) {
    if (!force && this.globalData.user && this.globalData.user.id) {
      return Promise.resolve(this.globalData.user)
    }

    const that = this
    const userInfo = that.globalData.userInfo || {}

    return new Promise(resolve => {
      wx.login({
        success: res => resolve(res.code || ''),
        fail: () => resolve('')
      })
    }).then(code => {
      return that.rawRequest({
        url: '/api/v1/user/wechat-login',
        method: 'POST',
        data: {
          code: config.auth.useWechatCode ? code : '',
          client_id: that.globalData.clientId,
          nickname: userInfo.nickName || '',
          avatar_url: userInfo.avatarUrl || ''
        }
      })
    }).catch(() => {
      return that.rawRequest({
        url: '/api/v1/user/register',
        method: 'POST',
        data: {
          openid: `dev_${that.globalData.clientId}`,
          nickname: userInfo.nickName || '',
          avatar_url: userInfo.avatarUrl || ''
        }
      })
    }).then(res => {
      that.syncSession(res)
      return that.globalData.user
    })
  },

  rawRequest: function (options) {
    const baseUrl = this.getApiBaseUrl()

    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
          ...(options.header || {})
        },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
          } else {
            const message = (res.data && (res.data.detail || res.data.message)) || '请求失败'
            reject(new Error(message))
          }
        },
        fail: (err) => reject(err)
      })
    })
  },

  request: function (options) {
    const that = this
    return that.ensureUser(options.forceAuth).then(user => {
      return that.rawRequest({
        ...options,
        header: {
          'X-User-Id': user.id,
          ...(options.header || {})
        }
      })
    })
  },

  uploadFile: function (options) {
    const that = this
    return that.ensureUser().then(user => {
      const baseUrl = that.getApiBaseUrl()
      return new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${baseUrl}${options.url}`,
          filePath: options.filePath,
          name: options.name || 'file',
          formData: options.formData || {},
          header: {
            'X-User-Id': user.id,
            ...(options.header || {})
          },
          success: res => {
            let data = res.data
            try {
              data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            } catch (e) {}

            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(data)
            } else {
              const message = (data && (data.detail || data.message)) || '上传失败'
              reject(new Error(message))
            }
          },
          fail: err => reject(err)
        })
      })
    })
  },

  refreshProfile: function () {
    const that = this
    return that.request({ url: '/api/v1/user/profile' }).then(res => {
      that.syncSession(res)
      return res
    })
  },

  payForVip: function () {
    const that = this
    return that.request({
      url: '/api/v1/order/create',
      method: 'POST',
      data: {
        type: 'vip_monthly',
        amount: config.payment.vipMonthlyPrice
      }
    }).then(res => {
      if (res.payment && res.payment.paySign !== 'mock_sign') {
        return new Promise((resolve, reject) => {
          wx.requestPayment({
            ...res.payment,
            success: () => resolve(res.order),
            fail: err => reject(err)
          })
        })
      }

      return that.rawRequest({
        url: '/api/v1/order/callback',
        method: 'POST',
        data: {
          order_no: res.order.order_no,
          status: 'paid',
          payment_id: `mock_${Date.now()}`
        }
      }).then(() => res.order)
    }).then(order => {
      return that.refreshProfile().then(() => order)
    })
  },

  showPaymentModal: function (callback) {
    wx.showModal({
      title: '开通会员',
      content: `今日免费次数已用完。开通月度会员 ¥${this.globalData.vipPrice} 后可继续使用。`,
      confirmText: '开通会员',
      cancelText: '稍后',
      success: res => {
        if (!res.confirm) {
          if (callback) callback(false)
          return
        }

        wx.showLoading({ title: '处理中...' })
        this.payForVip()
          .then(() => {
            wx.hideLoading()
            wx.showToast({ title: '已开通', icon: 'success' })
            if (callback) callback(true)
          })
          .catch(err => {
            wx.hideLoading()
            wx.showToast({ title: err.message || '支付失败', icon: 'none' })
            if (callback) callback(false)
          })
      }
    })
  }
})
