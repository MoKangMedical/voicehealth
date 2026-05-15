# VoiceHealth 健康数据 API 对接规范

版本：`vh.health.v1`

本文档用于把小程序中沉淀的语音、面部、视频、综合评估和趋势数据，整理成未来可被其他产品或模块调用的结构化 API。当前定位是健康管理参考、趋势观察和风险提示，不用于疾病确诊、治疗决策或急症分诊。

## 设计目标

- 统一字段：小程序、H5、企业健康管理、打卡、内容推荐、随访和数据看板使用同一套健康数据 schema。
- 保护隐私：默认只输出报告摘要、评分、维度、风险信号和趋势，不输出原始音频、图片、视频文件。
- 方便扩展：用 `schemaVersion` 标记版本，未来可以增加 OAuth2、API Key、Webhook、数据订阅和第三方 scope。
- 保持合规边界：所有接口都附带 `notice`，提醒调用方取得用户授权，并避免诊断式表达。

## 鉴权与授权

当前小程序和本地开发阶段使用：

```http
X-User-Id: <voicehealth_user_id>
```

生产级第三方对接建议增加：

- `Authorization: Bearer <token>` 或 API Key。
- 用户单独授权页，明确数据类型、使用目的、有效期和撤回方式。
- scope 控制，例如 `health.summary.read`、`health.timeline.read`、`health.report.read`、`health.export.read`。
- 审计日志，记录第三方应用、用户、接口、时间、授权来源和数据范围。

## 能力发现接口

### 获取集成清单

```http
GET /api/v1/integrations/manifest
```

用途：第三方模块启动时读取 API 版本、鉴权建议、scope 和可用端点。

### 获取能力目录

```http
GET /api/v1/integrations/capabilities
```

用途：读取 VoiceHealth 可提供的模块能力，包括声纹健康参考项、面部状态评估、视频健康观察、综合健康评估，以及证据库概览。

核心返回字段：

```json
{
  "schemaVersion": "vh.health.v1",
  "reportTypes": [
    { "type": "voice", "name": "声纹健康参考" },
    { "type": "face", "name": "面部状态评估" },
    { "type": "video", "name": "视频健康观察" },
    { "type": "combined", "name": "综合健康评估" }
  ],
  "scopes": [
    "health.summary.read",
    "health.timeline.read",
    "health.report.read",
    "health.export.read",
    "health.capability.read",
    "health.lifestyle.read",
    "health.lifestyle.write",
    "health.plan.read",
    "health.improvement.read",
    "health.improvement.write",
    "health.evidence_plan.read"
  ]
}
```

## 用户健康数据接口

以下接口均需要 `X-User-Id`。

### 健康总览

```http
GET /api/v1/health-data/summary
```

用途：给首页、个人中心、健康驾驶舱、企业端看板提供用户总览。

返回内容：

- `summary.totalReports`：总报告数。
- `summary.averageScore`：平均评分。
- `summary.bestScore`：历史最佳评分。
- `modules[]`：各模块报告数量、最近分数、最近报告 ID。
- `latestReports[]`：各模块最近报告摘要。

### 最近报告

```http
GET /api/v1/health-data/latest?type=all
GET /api/v1/health-data/latest?type=voice&includeFeatures=true
```

参数：

- `type`：`all`、`voice`、`face`、`video`、`combined`。
- `includeFeatures`：仅在需要声学指标明细时开启，默认 `false`。

用途：接入报告详情、健康助手、内容推荐、复测提醒等模块。

### 趋势时间线

```http
GET /api/v1/health-data/timeline?days=30&type=all
```

参数：

- `days`：趋势窗口，1 到 365 天。
- `type`：报告类型，默认 `all`。

用途：接入趋势图、打卡、随访、健康干预、复测提醒。

### 数据导出包

```http
GET /api/v1/health-data/export?type=all&limit=50&days=365
```

用途：用户授权后，把结构化健康数据同步给其他模块，例如：

- 大健康会员中心。
- 家庭健康档案。
- 企业健康管理看板。
- AI 健康助手。
- 运动、睡眠、饮食和心理模块。
- 医生端或线下服务工作台。

默认不输出原始媒体文件，只输出结构化结果。

## 健康改善行动计划

当评分偏低、风险信号升高或生活方式记录提示睡眠、运动、饮水、压力等问题时，可调用行动计划接口生成可执行建议。

```http
GET /api/v1/health-data/action-plan?reportId=<report_id>&days=30
```

如果不传 `reportId`，接口会基于用户最近一份报告生成方案。

返回内容包括：

- `scoreStatus`：当前评分等级和解释。
- `problemSignals`：主要问题信号。
- `lowDimensions`：低分维度。
- `goals`：短期目标。
- `actions`：可执行行动，包括原因、步骤、优先级和目标。
- `recheckPlan`：复测节奏。
- `whenToSeekCare`：需要及时就医的情况。
- `evidence`：行动建议参考的官方指南来源。

示例结构：

```json
{
  "actionPlan": {
    "scoreStatus": {
      "score": 66,
      "level": "attention",
      "label": "需要关注",
      "message": "分数偏低，建议连续复测并执行短期恢复计划。"
    },
    "goals": [
      {
        "id": "stabilize_score",
        "title": "先让分数稳定",
        "target": "未来7天在相同条件下复测，观察是否回到70分以上",
        "windowDays": 7
      }
    ],
    "actions": [
      {
        "id": "sleep_recovery",
        "category": "睡眠恢复",
        "priority": "high",
        "title": "优先恢复睡眠和日间精力",
        "steps": ["连续7天记录睡眠时长、入睡时间和日间困倦。"]
      }
    ]
  }
}
```

## 循证健康方案库

方案库把平台可安全追踪的健康改善动作整理成标准模块，每条方案包含适用场景、目标、执行步骤、跟踪指标、注意事项和证据来源。

当前覆盖：

- 运动：有氧活动、力量训练、减少久坐。
- 饮食：健康饮食结构、蔬果纤维、控盐、减少含糖饮料。
- 饮水：饮水与嗓音恢复。
- 睡眠：睡眠恢复与规律作息。
- 压力：压力恢复窗口。
- 烟酒：减少饮酒、戒烟支持与转介。
- 嗓音：嗓音保护。
- 安全边界：及时就医边界。

### 获取全部方案

```http
GET /api/v1/health-plans
GET /api/v1/health-plans?domain=运动
```

### 获取单个方案

```http
GET /api/v1/health-plans/<plan_id>
```

### 按用户报告匹配方案

```http
GET /api/v1/health-data/evidence-plans?reportId=<report_id>&days=30&limit=8
```

匹配依据：

- 评分等级。
- 报告中的风险信号和低分维度。
- 饮食、运动、饮水、睡眠、压力、饮酒、咽喉刺激等生活方式记录。

返回字段：

- `matchScore`：匹配强度。
- `matchReasons`：匹配原因。
- `steps`：可执行动作。
- `metrics`：建议追踪指标。
- `cautions`：不适用或需咨询专业人士的情况。
- `sources`：证据来源。

## 改善闭环模式

行动计划解决“应该做什么”，改善闭环解决“有没有执行、有没有改善、下一轮怎么调”。闭环流程为：

1. `detect`：完成一次语音、面部、视频或综合评估。
2. `plan`：根据评分、风险信号和生活方式记录生成行动计划。
3. `act`：用户每天勾选已完成行动。
4. `track`：同步记录饮食、运动、睡眠、压力和症状。
5. `recheck`：按计划复测，观察评分变化。
6. `adjust`：根据完成度和分数变化调整下一轮计划。

### 创建改善周期

```http
POST /api/v1/improvement/cycles
```

请求：

```json
{
  "reportId": "可选报告ID",
  "days": 14
}
```

如果不传 `reportId`，系统会使用最近一份报告创建周期。创建新周期时，旧的 `active` 周期会标记为 `replaced`。

### 获取当前周期

```http
GET /api/v1/improvement/active?autoCreate=true
```

`autoCreate=true` 时，如果用户已有报告但没有进行中周期，会自动创建一个14天改善周期。

### 保存每日执行进度

```http
POST /api/v1/improvement/cycles/<cycle_id>/progress
```

请求：

```json
{
  "checkinDate": "2026-05-13",
  "completedActionIds": ["sleep_recovery", "hydration_target"],
  "skippedActionIds": [],
  "moodScore": 3,
  "energyScore": 3,
  "note": "今天完成步行和补水，晚上准备早睡"
}
```

### 获取闭环复盘

```http
GET /api/v1/improvement/cycles/<cycle_id>/review
```

复盘字段：

- `completionRate`：本周期行动完成度。
- `scoreDelta`：最新评分相对基线的变化。
- `loopStatus`：`in_progress`、`improving`、`needs_consistency`、`needs_review`。
- `recommendations`：下一步调整建议。
- `closedLoop`：发现问题、生成方案、每日执行、生活方式记录、复测、调整的完成状态。

## 每日生活方式打卡

生活方式数据用于解释声纹和多模态健康趋势，例如睡眠不足、运动负荷、饮水不足、饮酒、辛辣油腻饮食、压力升高等因素对声音状态和主观疲劳的影响。

### 保存或更新每日记录

```http
POST /api/v1/lifestyle/checkin
X-User-Id: <voicehealth_user_id>
Content-Type: application/json
```

示例请求：

```json
{
  "checkinDate": "2026-05-13",
  "breakfast": "鸡蛋、燕麦、牛奶",
  "lunch": "米饭、鸡胸肉、青菜",
  "dinner": "鱼、蔬菜、面条",
  "snack": "咖啡、水果",
  "dietTags": ["清淡", "高蛋白", "蔬果充足"],
  "waterMl": 1800,
  "caffeineCups": 1,
  "alcohol": false,
  "spicyOily": false,
  "lateMeal": false,
  "exerciseType": "步行",
  "exerciseMinutes": 35,
  "exerciseIntensity": "中等强度",
  "steps": 7800,
  "sleepHours": 7.5,
  "stressLevel": 2,
  "mood": "平稳",
  "symptoms": ["咽干"],
  "notes": "今天讲话较多，晚饭较早"
}
```

### 获取某日记录

```http
GET /api/v1/lifestyle/checkin?date=2026-05-13
```

### 获取记录列表

```http
GET /api/v1/lifestyle/checkins?days=30&limit=100
```

### 获取生活方式汇总

```http
GET /api/v1/lifestyle/summary?days=30
```

汇总字段包括：

- `checkinDays`：周期内记录天数。
- `streak`：连续打卡天数。
- `avgWaterMl`：平均饮水量。
- `exerciseDays`：有运动记录的天数。
- `avgExerciseMinutes`：平均运动时长。
- `avgSteps`：平均步数。
- `avgSleepHours`：平均睡眠时长。
- `avgStressLevel`：平均压力等级。

## 公共报告字段

所有报告都会被转换为稳定公共字段：

```json
{
  "id": "report_id",
  "type": "voice",
  "typeName": "声纹健康参考",
  "score": 82.5,
  "scoreLevel": "good",
  "summary": "本次声纹健康参考完成",
  "createdAt": "2026-05-13T10:00:00",
  "positioning": "health_reference"
}
```

`scoreLevel` 枚举：

- `excellent`：90 分及以上。
- `good`：80 到 89 分。
- `watch`：70 到 79 分。
- `attention`：60 到 69 分。
- `priority`：60 分以下。
- `unknown`：无有效评分。

## 声纹报告扩展字段

```json
{
  "dimensions": [],
  "signals": [
    {
      "id": "voice_fatigue",
      "name": "声音疲劳参考",
      "category": "嗓音与喉部",
      "level": "medium",
      "score": 58,
      "markers": ["jitter", "shimmer"],
      "suggestion": "建议观察复测趋势"
    }
  ],
  "quality": {},
  "features": []
}
```

说明：`features` 只有在 `includeFeatures=true` 时返回，避免默认输出过多细粒度声学特征。

## 对接建议

- 首页模块只调用 `/health-data/summary`。
- 图表模块只调用 `/health-data/timeline`。
- 报告详情模块调用 `/health-data/latest` 或原有 `/report/{id}`。
- 第三方同步调用 `/health-data/export`，并在业务侧保存 `schemaVersion`。
- 新模块上线前先读 `/integrations/manifest`，确认版本、scope 和可用端点。

## 合规边界

- 不把评分解释为诊断结果。
- 不用“确诊、治疗、治愈、准确率”做接口文案或页面文案。
- 对外共享前取得用户明确授权，并提供撤回和删除路径。
- 若未来进入疾病筛查、辅助诊断或治疗决策，应按医疗器械软件和 AI 医疗器械路径重新评估。
