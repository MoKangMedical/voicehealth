# VoiceHealth 微信小程序上线发布清单

本文档用于把 VoiceHealth 发布成真实线上微信小程序：用户在小程序内朗读约 30 秒，系统上传音频到 VoiceHealth API，完成语音健康分析，返回声音健康参考报告、趋势和改善建议。

## 1. 产品边界

上线版本统一定位为：

- 声音健康管理参考平台
- 通过语音特征观察状态趋势
- 结合饮食、运动、睡眠、压力打卡形成改善闭环

所有页面、报告、课程、宣传内容必须避免：

- 不写“确诊、诊断、治疗、治愈、疾病筛查、替代体检、准确率保证”
- 不把单次分数解释为疾病结论
- 高风险提示必须引导复测、排除录音误差，并建议明显不适时及时就医

## 2. 小程序端已具备的核心能力

| 能力 | 文件 | 状态 |
| --- | --- | --- |
| 微信登录/本地开发身份 | `miniprogram/app.js` | 已接入 |
| 30 秒录音 | `pages/index/index.js` | 已接入 `wx.getRecorderManager()` |
| 朗读文本 | `pages/index/index.js` | 已接入 `/api/v1/verification/text` |
| 音频上传分析 | `pages/index/index.js` | 已接入 `/api/v1/voice/analyze` |
| 报告查看 | `pages/report/` | 已接入 |
| 历史与趋势 | `pages/history/`、`/api/v1/health-data/*` | 已接入 |
| 饮食运动打卡 | `pages/checkin/` | 已接入 |
| 改善闭环 | `pages/improvement/` | 已接入 |
| 健康学院课程 | `pages/articles/`、`pages/course-detail/` | 已接入 |
| 隐私政策 | `pages/privacy/` | 已接入 |

## 3. 后端生产要求

生产 API 域名建议统一为：

```text
https://voicehealth.ai
```

服务器需要满足：

1. 已部署本仓库 FastAPI 服务。
2. 进程监听 `127.0.0.1:8100` 或生产指定端口。
3. Nginx/Caddy/网关把 `https://voicehealth.ai/api/` 反向代理到 FastAPI。
4. HTTPS 证书有效，TLS 配置符合微信小程序要求。
5. 音频上传大小限制不少于 50MB。
6. 健康检查返回 VoiceHealth JSON：

```bash
curl https://voicehealth.ai/api/v1/health
curl https://voicehealth.ai/api/health
```

期望包含：

```json
{
  "status": "healthy",
  "service": "VoiceHealth"
}
```

生产服务器环境变量示例见根目录 `.env.production.example`。

## 4. 微信公众平台配置

进入 [微信公众平台](https://mp.weixin.qq.com/)：

1. 使用真实小程序账号，不使用测试号发布。
2. 确认服务类目优先选择健康管理、健康工具或软件服务类目；涉及医疗诊断、互联网医院、医疗器械时必须另行准备资质。
3. 在“开发管理 - 开发设置 - 服务器域名”配置：

| 域名类型 | 值 |
| --- | --- |
| request 合法域名 | `https://voicehealth.ai` |
| uploadFile 合法域名 | `https://voicehealth.ai` |
| downloadFile 合法域名 | 如后续报告下载/音频下载需要，再配置同域名 |

4. 在“隐私与用户保护”中声明：

- 麦克风/录音：用于生成声音健康参考报告
- 用户昵称头像：用于个人中心展示
- 健康打卡数据：用于趋势、改善方案和历史记录
- 不采集原始音频用于对外共享；如未来保存原始音频，需要在隐私政策中单独说明保存期限、删除路径和用途

## 5. 小程序项目配置

项目路径：

```text
/Users/apple/Desktop/OPC/voiceHealth/voiceHealth-miniprogram-v2
```

关键配置：

- `project.config.json` 已配置真实格式 AppID：`wxcadcf8da37a25c0e`
- `miniprogram/config.js` 已自动切换环境：
  - `develop` 开发版：使用 `devBaseUrl`
  - `trial` 体验版：使用 `baseUrl`
  - `release` 正式版：使用 `baseUrl`

因此发布前不要再手动把 `useDev` 改成 `true`。

## 6. 发布前本机检查

在仓库根目录执行：

```bash
python3 scripts/check_wechat_launch_ready.py --api-base https://voicehealth.ai
```

如果要把线上域名未就绪作为阻断项：

```bash
python3 scripts/check_wechat_launch_ready.py --api-base https://voicehealth.ai --strict-live
```

同时检查 JS 语法：

```bash
find voiceHealth-miniprogram-v2/miniprogram -name '*.js' -print0 | xargs -0 -n1 node --check
```

## 7. 微信开发者工具发布步骤

1. 打开微信开发者工具。
2. 导入项目：

```text
/Users/apple/Desktop/OPC/voiceHealth/voiceHealth-miniprogram-v2
```

3. 确认 AppID 为微信公众平台真实 AppID。
4. 编译首页，走完整测试：

- 授权用户信息
- 点击录音
- 朗读固定文本约 30 秒
- 停止录音
- 点击分析
- 进入报告页
- 返回首页看最近报告
- 打开历史/打卡/改善方案/健康学院/隐私页

5. 点击“上传”，版本号建议：

```text
1.0.0
```

版本描述建议：

```text
VoiceHealth 声音健康管理参考平台：支持30秒录音、声音健康参考报告、历史趋势、饮食运动打卡、改善方案和健康课程。
```

6. 回到微信公众平台“版本管理”，把开发版本提交审核。
7. 审核通过后点击发布。

## 8. 审核材料建议

审核备注建议：

```text
本小程序为健康管理参考工具，不提供医学诊断、疾病筛查、治疗或用药建议。用户授权麦克风后，可朗读固定文本约30秒，系统生成声音特征参考报告，并结合饮食、运动、睡眠、压力打卡提供健康管理建议。所有报告页和隐私页均展示非诊断声明。
```

测试账号：

```text
无需专用测试账号，首次进入可用微信授权登录。若审核需要固定账号，请在后端临时配置审核专用 openid 或测试用户。
```

## 9. 当前上线阻断项

发布前必须确认：

- `https://voicehealth.ai/api/v1/health` 返回 VoiceHealth 健康检查。
- `https://voicehealth.ai` 已在微信公众平台配置为 request/uploadFile 合法域名。
- 微信公众平台隐私接口和小程序隐私政策保持一致。
- 所有对外宣传均使用“健康管理参考”，不使用诊断或筛查承诺。

只要线上域名尚未绑定到本仓库 FastAPI 服务，就不能称为已上线，只能称为“代码和发布包已准备好”。

## 10. 2026-07-04 实测状态

已执行：

```bash
python3 scripts/check_wechat_launch_ready.py --api-base https://voicehealth.ai
python3 scripts/check_wechat_launch_ready.py --api-base https://voicehealth.ai --strict-live
```

结果：

- 非严格检查：`PASS=13 WARN=1 FAIL=0`
- 严格线上检查：`PASS=13 WARN=0 FAIL=1`
- `https://voicehealth.ai/api/v1/health` 当前返回 HTML，不是 VoiceHealth JSON
- 响应头显示 `server: LiteSpeed`，说明当前域名还没有代理到本仓库 FastAPI 服务

下一步必须完成服务器部署、域名解析/反向代理和微信公众平台合法域名配置，然后重新执行严格检查。
