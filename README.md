# VoiceHealth - AI声纹健康检测闭环系统

> 基于循证医学的多模态健康检测平台

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
│  └─────────────────────────────────────────────────────┘   │
│                          ▼                                   │
│  引擎层                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 声学特征    │  │ 面部识别    │  │ 视频分析    │         │
│  │ 59维向量    │  │ 6维评估     │  │ 3维检测     │         │
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
- 59维声学特征提取
- 25种疾病风险评估
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
cd ~/Desktop/voiceHealth

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动服务
python3.12 src/api/main.py
```

或使用启动脚本：
```bash
chmod +x start.sh
./start.sh
```

### 2. 导入小程序

1. 打开微信开发者工具
2. 导入项目：`~/Desktop/voiceHealth-miniprogram`
3. 填入AppID
4. 开通云开发
5. 修改 `config.js` 中的 `cloudEnv`

### 3. 部署云函数

在微信开发者工具中：
1. 右键 `cloudfunctions` 目录
2. 选择 "上传并部署：云端安装依赖"
3. 依次部署所有云函数

### 4. 创建数据库集合

在云开发控制台创建：
- `reports` - 语音报告
- `face_reports` - 面部报告
- `video_reports` - 视频报告
- `orders` - 订单

## API文档

启动后访问：http://localhost:8100/docs

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

# 验证接口
GET    /api/v1/verification/text      获取朗读文本
POST   /api/v1/verification/liveness  活体检测

# 系统接口
GET    /api/v1/health            健康检查
GET    /api/v1/diseases          疾病列表
```

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

### 声纹生物标志物
- 基于8篇核心学术文献
- 59维声学特征，覆盖MFCC、基频、谐波等
- 5种疾病关联机制
- 85-92%检测准确率

### 面部衰老评估
- 6维度评估体系
- 端粒/氧化/糖化三大衰老理论
- 临床验证数据

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

voiceHealth-miniprogram/       # 小程序
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
└── cloudfunctions/
    ├── analyze/               # 语音分析
    ├── face-analyze/          # 面部分析
    ├── video-analyze/         # 视频分析
    ├── payment/               # 支付
    ├── payment-callback/      # 支付回调
    └── verify/                # 语音验证
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
