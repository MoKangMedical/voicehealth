# VoiceHealth 微信小程序配置清单

## 本地开发

1. 启动后端：

```bash
cd /Users/apple/Desktop/OPC/voiceHealth
./start.sh
```

2. 微信开发者工具导入：

```text
/Users/apple/Desktop/OPC/voiceHealth/voiceHealth-miniprogram-v2
```

3. 本地模拟器配置：

- `voiceHealth-miniprogram-v2/miniprogram/config.js`
- `api.useDev = true`
- `api.devBaseUrl = 'http://127.0.0.1:8100'`
- 开发者工具里可关闭“校验合法域名、web-view、TLS 版本以及 HTTPS 证书”

4. 真机调试时，把 `api.devBaseUrl` 改成电脑局域网 IP，例如：

```js
devBaseUrl: 'http://192.168.2.11:8100'
```

手机和电脑必须连接同一个局域网，且电脑防火墙允许访问 `8100` 端口。

## 生产上线

1. 在微信公众平台创建/选择小程序，拿到真实 AppID。
2. 将 `voiceHealth-miniprogram-v2/project.config.json` 里的 `appid` 改为真实 AppID。
3. 在服务器环境变量中配置：

```bash
WECHAT_APP_ID=你的真实AppID
WECHAT_APP_SECRET=你的真实AppSecret
VOICEHEALTH_PORT=8100
```

4. 将后端部署到 HTTPS 域名，例如：

```text
https://voicehealth.ai
```

5. 在微信公众平台后台配置服务器域名：

- request 合法域名：`https://voicehealth.ai`
- uploadFile 合法域名：`https://voicehealth.ai`
- downloadFile 合法域名：按实际需要填写

6. 发布前修改：

```js
// voiceHealth-miniprogram-v2/miniprogram/config.js
api: {
  baseUrl: 'https://voicehealth.ai',
  devBaseUrl: 'http://127.0.0.1:8100',
  useDev: false
}
```

7. 在微信开发者工具中重新编译，确认控制台没有请求失败错误后，再点击“上传”。

## 当前本机状态

- 小程序项目已导入微信开发者工具。
- 本地 API 已验证：`http://127.0.0.1:8100/api/v1/health`
- 首页、记录页、我的页已经在模拟器验证能访问后端。
- 当前使用测试号 AppID，上传发布前必须替换为真实 AppID。
