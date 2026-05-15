const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const db = cloud.database()

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()
  const { type, amount, description } = event

  const orderId = `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // 保存订单
  await db.collection('orders').add({
    data: {
      orderId,
      userId: OPENID,
      type,
      amount,
      description,
      status: 'pending',
      createTime: db.serverDate()
    }
  })

  // 返回支付参数（模拟）
  return {
    success: true,
    orderId,
    payment: {
      timeStamp: String(Math.floor(Date.now() / 1000)),
      nonceStr: Math.random().toString(36).substr(2, 15),
      package: `prepay_id=${orderId}`,
      signType: 'MD5',
      paySign: 'mock_sign_' + orderId
    }
  }
}
