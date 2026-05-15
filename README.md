# VoiceHealth - AI声纹大健康参考闭环系统

> 面向微信小程序的多模态健康参考平台

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    VoiceHealth 闭环系统                       │
├─────────────────────────────────────────────────────────────┤
│  用户层                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 微信小程序   │  │  Web前端    │  │  API集成    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         └────────────────┼────────────────┘                 │
│                          ▼                                   │
│  API层 (FastAPI)                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ /api/v1/user      用户系统 (注册/登录/VIP)           │   │
│  │ /api/v1/voice     语音分析 (录音/验证/分析)          │   │
│  │ /api/v1/face      面部分析 (拍照/分析)               │   │
│  │ /api/v1/video     视频分析 (录制/分析)               │   │
│  │ /api/v1/order     订单支付 (创建/回调)               │   │
│  │ /api/v1/stats     统计趋势 (数据/图表)               │   │
│  │ /api/v1/health-data 健康数据API (未来模块对接)       │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▼                                   │
│  引擎层                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 声音健康    │  │ 面部识别    │  │ 视频分析    │         │
│  │ 25项参考    │  │ 6维评估     │  │ 3维检测     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          ▼                                   │
│  数据层 (SQLite)                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 用户表      │  │ 报告表      │  │ 订单表      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 功能模块

### 1. 用户系统
- 微信授权登录
- 用户信息管理
- VIP会员系统
- 免费次数控制

### 2. 语音健康检测
- 实时录音
- 活体检测 (防作弊)
- 朗读验证 (确保真实性)
- 多维声学特征提取
- 25项声音大健康风险参考
- AI健康建议生成

### 3. 面部衰老分析
- 相机拍照/相册选择
- 6维度评估 (皱纹/色斑/紧致度/眼部/法令纹/肤色)
- 年龄预测
- 改善建议

### 4. 视频健康分析
- 相机录制
- 皮肤状态检测
- 眼睛状态检测
- 头发状态检测
- 综合评分

### 5. 综合健康评估
- 声纹+面部双维度
- 六维健康指标
- 生物学年龄预测
- 个性化建议

### 6. 支付系统
- 单次购买 (9.9元)
- 月度VIP (29.9元)
- 微信支付集成
- 订单管理

## 快速开始

### 1. 启动后端服务

```bash
cd /Users/apple/Desktop/OPC/voiceHealth

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 可选：复制生产环境变量模板
cp .env.example .env

# 启动服务
python3.12 src/api/main.py
```

或使用启动脚本：
```bash
chmod +x start.sh
./start.sh
```

### 2. 导入微信小程序 v2

1. 打开微信开发者工具
2. 导入项目：`voiceHealth-miniprogram-v2`
3. 本地开发可使用测试号 AppID；上传发布前必须替换成真实 AppID
4. 修改 `voiceHealth-miniprogram-v2/miniprogram/config.js`
   - 本地开发：`api.useDev = true`，模拟器可用 `http://127.0.0.1:8100`
   - 真机调试：把 `api.devBaseUrl` 改为电脑局域网地址，例如 `http://192.168.1.8:8100`
   - 线上发布：把 `api.baseUrl` 改为 HTTPS 后端域名，并加入小程序 request/uploadFile 合法域名
5. 后端可选配置 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`。未配置时，小程序会使用本地开发身份完成注册和调试。

详细配置清单见：`WECHAT_MINIPROGRAM_SETUP.md`

### 3. 直接运行闭环

小程序 v2 已直连 FastAPI，不再依赖云函数。启动后端后，可在小程序中完成：
- 微信/开发身份登录
- 30秒录音上传与语音报告
- 面部照片上传与衰老评估
- 视频上传与健康状态分析
- 历史记录、报告详情、个人中心统计
- 每日饮食、运动、睡眠、压力和症状打卡

## API文档

启动后访问：http://127.0.0.1:8100/docs

### 核心接口

```
# 用户系统
POST   /api/v1/user/register     用户注册/登录
GET    /api/v1/user/profile      获取用户信息
PUT    /api/v1/user/profile      更新用户信息

# 语音分析
POST   /api/v1/voice/analyze     语音分析
GET    /api/v1/voice/report/:id  获取语音报告
GET    /api/v1/voice/history     检测历史

# 面部分析
POST   /api/v1/face/analyze      面部分析
GET    /api/v1/face/report/:id   获取面部报告

# 视频分析
POST   /api/v1/video/analyze     视频分析
GET    /api/v1/video/report/:id  获取视频报告

# 订单支付
POST   /api/v1/order/create      创建订单
POST   /api/v1/order/callback    支付回调
GET    /api/v1/order/list        订单列表

# 统计趋势
GET    /api/v1/stats             用户统计
GET    /api/v1/trends            趋势数据

# 健康数据开放接口
GET    /api/v1/integrations/manifest      API集成清单
GET    /api/v1/integrations/capabilities  平台能力目录
GET    /api/v1/health-data/summary        用户健康数据总览
GET    /api/v1/health-data/latest         最近健康报告
GET    /api/v1/health-data/timeline       健康趋势时间线
GET    /api/v1/health-data/action-plan    健康改善行动计划
GET    /api/v1/health-data/evidence-plans 用户匹配循证方案
GET    /api/v1/health-data/export         授权数据导出包
GET    /api/v1/health-plans               循证健康方案库
GET    /api/v1/health-plans/:id           单个循证方案

# 改善闭环模式
POST   /api/v1/improvement/cycles                 创建改善周期
GET    /api/v1/improvement/active                 当前改善周期
GET    /api/v1/improvement/cycles                 改善周期列表
POST   /api/v1/improvement/cycles/:id/progress    保存每日执行进度
GET    /api/v1/improvement/cycles/:id/review      获取闭环复盘
POST   /api/v1/improvement/cycles/:id/status      更新周期状态

# 每日生活方式打卡
POST   /api/v1/lifestyle/checkin          保存饮食/运动/睡眠/压力记录
GET    /api/v1/lifestyle/checkin          获取某日生活方式记录
GET    /api/v1/lifestyle/checkins         获取生活方式记录列表
GET    /api/v1/lifestyle/summary          获取生活方式汇总

# 验证接口
GET    /api/v1/verification/text      获取朗读文本
POST   /api/v1/verification/liveness  活体检测

# 系统接口
GET    /api/v1/health            健康检查
GET    /api/v1/diseases          声音健康参考项列表
GET    /api/v1/evidence          理论基础、参考文献与指南
```

健康数据 API 对接规范见：`docs/HEALTH_DATA_API.md`

## 数据库模型

### users (用户表)
- id, openid, nickname, avatar_url
- is_vip, vip_expire_at, free_count
- total_reports, created_at

### voice_reports (语音报告)
- id, user_id, overall_score
- features, risks, ai_insight
- liveness_score, reading_match_score

### face_reports (面部报告)
- id, user_id, overall_score
- predicted_age, dimensions, suggestions

### video_reports (视频报告)
- id, user_id, overall_score
- biological_age, skin/eye/hair_result

### orders (订单表)
- id, order_no, user_id, type, amount
- status, payment_id, paid_at

## 科学依据

完整证据库、参考文献、采集指南、打卡指南和合规边界见：
`docs/VOICEHEALTH_EVIDENCE_BASE.md`

### 声纹生物标志物
- 覆盖基频、Jitter/Shimmer、HNR、能量、停顿、频谱、韵律和信号质量等可解释声学特征
- 支持呼吸与气道、嗓音与喉部、神经运动、心理压力、睡眠疲劳、认知沟通、心肺活力、总体活力等维度
- 输出25项声音大健康风险参考和趋势字段
- 当前结果定位为健康管理参考，不构成医学筛查或诊断

### 面部衰老评估
- 6维度评估体系
- 端粒/氧化/糖化三大衰老理论
- 结果用于健康管理参考，需结合真实场景持续验证

### 检测局限性
- 明确说明"仅供参考，不构成医学诊断"
- 详细的局限性说明
- 免责声明组件

## 项目结构

```
voiceHealth/                    # 后端
├── src/
│   ├── api/
│   │   ├── main.py            # FastAPI入口
│   │   └── routes.py          # API路由
│   └── core/
│       ├── database.py        # 数据库模型
│       ├── feature_extractor.py
│       ├── disease_detector.py
│       ├── voice_verifier.py
│       ├── video_analyzer.py
│       └── scientific_basis.py
├── data/                      # SQLite数据
├── start.sh                   # 启动脚本
└── requirements.txt

voiceHealth-miniprogram-v2/    # 微信小程序，直连 FastAPI
├── miniprogram/
│   ├── pages/
│   │   ├── index/             # 首页
│   │   ├── report/            # 报告
│   │   ├── history/           # 历史
│   │   ├── profile/           # 个人中心
│   │   ├── science/           # 科学依据
│   │   ├── face/              # 面部分析
│   │   ├── combined/          # 综合评估
│   │   └── video/             # 视频分析
│   ├── components/
│   │   └── disclaimer/        # 免责声明
│   └── config.js
└── project.config.json
```

## 商业模式

### 免费用户
- 每天1次免费检测
- 基础报告查看

### VIP会员 (29.9元/月)
- 无限次检测
- 完整报告
- 趋势分析
- AI深度建议

### 单次购买 (9.9元/次)
- 完整报告
- 无限制

## 审核要点

1. **服务类目**：医疗健康 -> 健康管理
2. **资质要求**：定位为"健康参考工具"
3. **隐私协议**：必须有隐私政策页面
4. **免责声明**：每个页面都要有"仅供参考"提示
5. **数据安全**：用户数据加密存储

## 联系方式

- 邮箱：support@voicehealth.ai
- 微信：VoiceHealth_AI

## License

MIT
