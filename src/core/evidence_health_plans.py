"""
Evidence-based wellness plan catalog.

These plans are designed for VoiceHealth's health-management positioning. They
support behavior change, tracking, and follow-up, but they are not diagnosis or
treatment plans.
"""

from typing import Any, Dict, List, Optional


EVIDENCE_HEALTH_PLANS: List[Dict[str, Any]] = [
    {
        "id": "activity_aerobic_base",
        "domain": "运动",
        "title": "有氧活动基础方案",
        "evidenceLevel": "official_guideline",
        "summary": "从可坚持的步行、骑行、游泳或其他中等强度活动开始，逐步形成规律运动。",
        "suitableFor": ["心肺活力偏低", "久坐", "压力高", "睡眠质量差", "综合评分偏低"],
        "target": "逐步接近每周150分钟中等强度有氧活动，或按个人能力从每周3次10到20分钟开始。",
        "steps": [
            "第1周先完成3次10到20分钟轻中等强度步行。",
            "能轻松完成后，每周增加10到20分钟总量。",
            "运动后至少间隔30分钟再录音，避免把运动后气息波动误判为趋势变化。",
            "记录运动类型、分钟数、强度和主观疲劳。",
        ],
        "metrics": ["exerciseDays", "exerciseMinutes", "steps", "voiceScoreTrend"],
        "cautions": ["胸痛、明显气促、头晕或心悸时停止运动并就医。慢病或孕期用户应遵医嘱。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["心肺", "呼吸", "气短", "活力", "疲劳"],
            "lifestyleFlags": ["low_exercise"],
        },
        "sources": [
            {
                "name": "WHO Physical Activity Fact Sheet",
                "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            }
        ],
    },
    {
        "id": "activity_strength_twice_week",
        "domain": "运动",
        "title": "力量训练与肌肉维护方案",
        "evidenceLevel": "official_guideline",
        "summary": "在有氧活动之外，加入适合自己的抗阻或力量训练，帮助维持肌肉、代谢和功能状态。",
        "suitableFor": ["活动不足", "代谢状态偏低", "衰老相关维度偏低", "长期久坐"],
        "target": "每周安排2天肌肉强化活动，动作和负荷按个人能力调整。",
        "steps": [
            "从深蹲、靠墙俯卧撑、弹力带划船、提踵等低门槛动作开始。",
            "每次选择4到6个动作，每个动作1到2组，避免做到疼痛。",
            "训练日之间留出恢复时间。",
            "记录训练天数、动作和主观疲劳。",
        ],
        "metrics": ["strengthDays", "exerciseIntensity", "fatigueNote"],
        "cautions": ["有关节疼痛、骨质疏松、心血管疾病或近期手术史时，应先咨询专业人员。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["代谢", "衰老", "活力", "疲劳"],
            "lifestyleFlags": ["low_exercise"],
        },
        "sources": [
            {
                "name": "WHO Physical Activity Fact Sheet",
                "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            }
        ],
    },
    {
        "id": "sedentary_breaks",
        "domain": "运动",
        "title": "减少久坐打断方案",
        "evidenceLevel": "official_guideline",
        "summary": "用短时间站立、步行、拉伸打断久坐，作为运动不足用户的第一步。",
        "suitableFor": ["久坐", "工作压力高", "运动基础弱", "日间疲劳"],
        "target": "工作日每60到90分钟至少起身活动2到5分钟。",
        "steps": [
            "设置站起提醒，不追求高强度，先追求稳定执行。",
            "用倒水、短步行、肩颈拉伸替代连续久坐。",
            "把久坐打断次数记入备注，观察日间疲劳和晚间睡眠变化。",
        ],
        "metrics": ["breakCount", "steps", "energyScore"],
        "cautions": ["站立或活动时如头晕、胸闷，应停止并评估原因。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["疲劳", "压力", "活力"],
            "lifestyleFlags": ["low_exercise"],
        },
        "sources": [
            {
                "name": "WHO Physical Activity Fact Sheet",
                "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            }
        ],
    },
    {
        "id": "sleep_regular_7h",
        "domain": "睡眠",
        "title": "睡眠恢复与规律作息方案",
        "evidenceLevel": "official_guideline",
        "summary": "成年人通常需要每晚至少7小时睡眠；规律睡眠有助于疲劳、压力和声音状态恢复。",
        "suitableFor": ["睡眠不足", "日间疲劳", "压力高", "声音能量低", "停顿增多"],
        "target": "7天内把平均睡眠逐步接近7小时或以上。",
        "steps": [
            "固定起床时间，先稳定节律，再提前入睡时间。",
            "睡前减少高强度工作、争论、饮酒和长时间屏幕刺激。",
            "下午或晚间减少咖啡因摄入，并记录咖啡/茶杯数。",
            "连续记录睡眠小时、日间困倦和声音评分。",
        ],
        "metrics": ["sleepHours", "daytimeFatigue", "voiceEnergy", "stressLevel"],
        "cautions": ["长期失眠、打鼾憋醒、白天明显嗜睡或情绪显著受影响时，建议咨询专业医生。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["睡眠", "疲劳", "困倦", "能量"],
            "lifestyleFlags": ["low_sleep"],
        },
        "sources": [
            {
                "name": "CDC About Sleep",
                "url": "https://www.cdc.gov/sleep/about/index.html",
            }
        ],
    },
    {
        "id": "diet_healthy_pattern",
        "domain": "饮食",
        "title": "健康饮食结构方案",
        "evidenceLevel": "official_guideline",
        "summary": "以蔬菜、水果、全谷物、豆类、坚果和优质蛋白为基础，减少高盐、高糖和高饱和脂肪食物。",
        "suitableFor": ["代谢状态偏低", "体力恢复差", "饮食记录不规律", "综合评分偏低"],
        "target": "连续14天记录三餐，逐步提高蔬果、全谷物和优质蛋白比例。",
        "steps": [
            "每餐先记录主食、蛋白、蔬菜/水果和饮品。",
            "每天至少有一餐加入蔬菜或水果。",
            "用全谷物、豆类、鱼、蛋、奶或瘦肉替代部分高油盐加工食品。",
            "每周回顾饮食标签，寻找高油盐、甜食、夜宵和饮酒触发因素。",
        ],
        "metrics": ["dietTags", "mealCompleteness", "waterMl", "energyScore"],
        "cautions": ["糖尿病、肾病、痛风、孕期或特殊疾病饮食应遵医嘱，不使用通用方案替代营养治疗。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["代谢", "活力", "衰老", "疲劳"],
            "lifestyleFlags": ["poor_diet_record"],
        },
        "sources": [
            {
                "name": "WHO Healthy Diet",
                "url": "https://www.who.int/en/news-room/fact-sheets/detail/healthy-diet",
            },
            {
                "name": "Dietary Guidelines for Americans 2020-2025",
                "url": "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials",
            },
        ],
    },
    {
        "id": "diet_fruit_veg_fiber",
        "domain": "饮食",
        "title": "蔬果与膳食纤维提升方案",
        "evidenceLevel": "official_guideline",
        "summary": "增加蔬菜、水果、豆类和全谷物，帮助改善饮食质量和长期代谢健康。",
        "suitableFor": ["蔬果摄入少", "便秘倾向", "代谢维度偏低", "饮食结构单一"],
        "target": "逐步接近每天400克或5份蔬果的常用公共卫生目标。",
        "steps": [
            "早餐或加餐加入一份水果。",
            "午餐和晚餐至少一餐增加一份蔬菜。",
            "每周加入豆类、燕麦、杂粮或全谷物主食。",
            "增加纤维时同步增加饮水，并观察胃肠反应。",
        ],
        "metrics": ["dietTags", "vegetableFruitDays", "waterMl"],
        "cautions": ["胃肠疾病、肾病或需要限钾者，应遵医嘱选择蔬果种类和摄入量。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["代谢", "活力", "衰老"],
            "lifestyleFlags": ["poor_diet_record"],
        },
        "sources": [
            {
                "name": "WHO Healthy Diet",
                "url": "https://www.who.int/en/news-room/fact-sheets/detail/healthy-diet",
            }
        ],
    },
    {
        "id": "diet_sodium_reduce",
        "domain": "饮食",
        "title": "控盐与少加工食品方案",
        "evidenceLevel": "official_guideline",
        "summary": "减少高盐调味和高钠加工食品，支持长期心血管和代谢健康。",
        "suitableFor": ["高盐饮食", "外卖多", "加工食品多", "心血管维度需关注"],
        "target": "连续2周记录高盐来源，每周减少一种高盐习惯。",
        "steps": [
            "记录外卖、加工肉、咸菜、酱料、汤底等高钠来源。",
            "先从少喝汤底、酱料减半、少点腌制食品开始。",
            "用葱姜蒜、醋、香草或香辛料替代部分盐味。",
            "购买包装食品时优先查看钠含量。",
        ],
        "metrics": ["dietTags", "highSaltDays", "bloodPressureNote"],
        "cautions": ["正在使用低钠盐、利尿剂或有肾病、高钾风险者，应先咨询医生。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["心血管", "代谢", "水肿"],
            "lifestyleFlags": ["high_salt_or_oily"],
        },
        "sources": [
            {
                "name": "WHO Healthy Diet",
                "url": "https://www.who.int/en/news-room/fact-sheets/detail/healthy-diet",
            },
            {
                "name": "Dietary Guidelines for Americans 2020-2025",
                "url": "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials",
            },
        ],
    },
    {
        "id": "diet_added_sugar_drinks",
        "domain": "饮食",
        "title": "减少含糖饮料与添加糖方案",
        "evidenceLevel": "official_guideline",
        "summary": "用白水、无糖茶或其他无糖饮品替代含糖饮料，减少额外能量摄入。",
        "suitableFor": ["甜饮多", "能量波动", "代谢状态需关注", "饮水不足"],
        "target": "7天内把含糖饮料替换为无糖饮品至少3次。",
        "steps": [
            "记录每天饮料种类和杯数。",
            "先把最容易替换的一杯含糖饮料换成白水或无糖饮品。",
            "保留口味需求时，优先选择无糖茶、气泡水或淡味饮品。",
            "观察下午疲劳、口渴和咽喉干涩变化。",
        ],
        "metrics": ["waterMl", "caffeineCups", "dietTags", "energyScore"],
        "cautions": ["儿童、孕期、糖尿病或特殊饮食管理用户，应使用个体化营养建议。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["代谢", "疲劳", "咽干"],
            "lifestyleFlags": ["low_water"],
        },
        "sources": [
            {
                "name": "CDC Water and Healthier Drinks",
                "url": "https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/index.html",
            },
            {
                "name": "Dietary Guidelines for Americans 2020-2025",
                "url": "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials",
            },
        ],
    },
    {
        "id": "hydration_voice_recovery",
        "domain": "饮水",
        "title": "饮水与嗓音恢复方案",
        "evidenceLevel": "official_guideline",
        "summary": "稳定饮水记录，减少含糖饮料，支持咽喉舒适度和日常恢复。",
        "suitableFor": ["咽干", "嗓音疲劳", "饮水少", "长时间讲话", "运动后声音疲劳"],
        "target": "连续7天记录饮水量，并观察咽干、清嗓和声音疲劳变化。",
        "steps": [
            "把饮水分散到上午、下午和晚饭前。",
            "长时间讲话或运动后，记录饮水和嗓音变化。",
            "减少含糖饮料，把白水或无糖饮品作为主要来源。",
            "在报告备注中记录咽干、清嗓、嘶哑等症状。",
        ],
        "metrics": ["waterMl", "symptoms", "voiceQuality", "hoarsenessSignal"],
        "cautions": ["心衰、肾病或医生限制饮水者，应以医嘱为准。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["咽干", "嗓音", "嘶哑", "干燥", "疲劳"],
            "lifestyleFlags": ["low_water", "throat_irritants"],
        },
        "sources": [
            {
                "name": "CDC Water and Healthier Drinks",
                "url": "https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/index.html",
            },
            {
                "name": "NIDCD Taking Care of Your Voice",
                "url": "https://www.nidcd.nih.gov/health/taking-care-your-voice",
            },
        ],
    },
    {
        "id": "stress_recovery_window",
        "domain": "压力",
        "title": "压力恢复窗口方案",
        "evidenceLevel": "official_public_health_guidance",
        "summary": "把压力记录、身体活动、睡眠和社会支持结合起来，降低持续压力对声音和恢复的影响。",
        "suitableFor": ["压力高", "倦怠", "语速/韵律异常", "睡眠受影响", "日间疲劳"],
        "target": "连续7天记录压力来源，并每天安排一个10分钟恢复窗口。",
        "steps": [
            "每天给压力打0到5分，并写下主要压力来源。",
            "选择10分钟散步、拉伸、呼吸放松、离屏休息或与可信任的人交流。",
            "把恢复窗口安排在固定时间，先追求稳定而不是时长。",
            "观察压力评分、睡眠和声音能量变化。",
        ],
        "metrics": ["stressLevel", "moodScore", "sleepHours", "energyScore"],
        "cautions": ["持续低落、焦虑、失眠、惊恐或自伤想法，应尽快寻求专业帮助。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["压力", "情绪", "倦怠", "焦虑", "抑郁"],
            "lifestyleFlags": ["high_stress"],
        },
        "sources": [
            {
                "name": "CDC Managing Stress",
                "url": "https://www.cdc.gov/mental-health/living-with/index.html",
            }
        ],
    },
    {
        "id": "alcohol_reduce",
        "domain": "烟酒",
        "title": "减少饮酒方案",
        "evidenceLevel": "official_public_health_guidance",
        "summary": "如果饮酒，减少饮酒通常比多饮酒更有利于健康；饮酒也可能影响睡眠、反流和嗓音状态。",
        "suitableFor": ["饮酒记录", "睡眠差", "反流/咽喉刺激", "压力饮酒", "疲劳"],
        "target": "连续14天记录饮酒天数和杯数，并减少一次非必要饮酒。",
        "steps": [
            "记录饮酒日期、杯数、场景和第二天睡眠/嗓音状态。",
            "先减少最容易替代的一次饮酒，用无酒精饮品替代。",
            "避免用酒精帮助入睡。",
            "若难以减少或出现戒断不适，应咨询专业机构。",
        ],
        "metrics": ["alcoholDays", "sleepHours", "throatSymptoms", "stressLevel"],
        "cautions": ["孕期、备孕、驾驶、服药或有酒精使用障碍风险者，应避免饮酒并咨询专业人员。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["反流", "咽喉", "睡眠", "疲劳"],
            "lifestyleFlags": ["alcohol"],
        },
        "sources": [
            {
                "name": "CDC Drinking Less Matters",
                "url": "https://www.cdc.gov/drink-less-be-your-best/drinking-less-matters/index.html",
            }
        ],
    },
    {
        "id": "tobacco_quit_referral",
        "domain": "烟酒",
        "title": "戒烟支持与转介方案",
        "evidenceLevel": "official_public_health_guidance",
        "summary": "戒烟可降低多种健康风险，并有助于呼吸、嗓音和心血管健康；平台提供记录和转介提示。",
        "suitableFor": ["吸烟", "二手烟暴露", "咳嗽", "气道刺激", "嗓音嘶哑"],
        "target": "设置一个戒烟准备日，记录触发场景，并连接专业戒烟资源。",
        "steps": [
            "记录每天吸烟支数、触发场景和替代动作。",
            "选择一个准备日，提前移除烟草和相关物品。",
            "把高风险场景写入备注，例如饭后、压力、饮酒或社交。",
            "考虑使用戒烟热线、医生咨询或已批准戒烟产品支持。",
        ],
        "metrics": ["smokingCount", "triggerNotes", "coughOrHoarseness", "voiceScoreTrend"],
        "cautions": ["尼古丁替代或药物戒烟应咨询专业人员，尤其是孕期、慢病或正在服药者。"],
        "match": {
            "scoreLevels": ["good", "watch", "attention", "priority"],
            "signalKeywords": ["气道", "咳嗽", "嘶哑", "喉", "呼吸"],
            "lifestyleFlags": ["smoking"],
        },
        "sources": [
            {
                "name": "CDC Benefits of Quitting Smoking",
                "url": "https://www.cdc.gov/tobacco/about/benefits-of-quitting.html",
            },
            {
                "name": "CDC How to Quit Smoking",
                "url": "https://www.cdc.gov/tobacco/about/how-to-quit.html",
            },
        ],
    },
    {
        "id": "voice_care",
        "domain": "嗓音",
        "title": "嗓音保护方案",
        "evidenceLevel": "official_health_information",
        "summary": "减少高强度用嗓、补水、避免刺激因素，并在持续嘶哑时线下评估。",
        "suitableFor": ["嘶哑", "嗓音疲劳", "咽干", "长时间讲话", "清嗓频繁"],
        "target": "连续3到7天执行嗓音保护，并复测声音稳定性。",
        "steps": [
            "减少长时间连续讲话、喊叫和频繁清嗓。",
            "长时间用嗓后安排安静恢复时间。",
            "记录饮水、睡前进食、辛辣油腻、饮酒和咽喉症状。",
            "使用相同环境复测，观察音质和停顿变化。",
        ],
        "metrics": ["symptoms", "waterMl", "voiceQuality", "riskSignals"],
        "cautions": ["持续嘶哑超过两周、吞咽困难、咽喉疼痛、咳血或呼吸困难，应咨询耳鼻喉医生。"],
        "match": {
            "scoreLevels": ["watch", "attention", "priority"],
            "signalKeywords": ["嗓音", "嘶哑", "咽喉", "反流", "干燥", "清嗓"],
            "lifestyleFlags": ["throat_irritants", "low_water"],
        },
        "sources": [
            {
                "name": "NIDCD Taking Care of Your Voice",
                "url": "https://www.nidcd.nih.gov/health/taking-care-your-voice",
            }
        ],
    },
    {
        "id": "urgent_red_flags",
        "domain": "安全边界",
        "title": "及时就医边界方案",
        "evidenceLevel": "clinical_safety_boundary",
        "summary": "识别小程序不应处理的危险信号，把用户引导到线下医疗或急救路径。",
        "suitableFor": ["严重不适", "急性症状", "连续低分", "症状快速加重"],
        "target": "出现危险信号时不继续依赖评分，优先线下医疗评估。",
        "steps": [
            "胸痛、明显气促、喘憋、嘴唇发紫等急性症状，应立即就医。",
            "突然言语含糊、口角歪斜、肢体无力或意识异常，应立即就医。",
            "持续嘶哑超过两周、吞咽困难、咽喉疼痛或咳血，建议耳鼻喉评估。",
            "持续低落、焦虑、失眠或自伤想法，应尽快寻求专业帮助。",
        ],
        "metrics": ["redFlagSymptoms", "careReferral"],
        "cautions": ["本方案不是诊断工具；任何急性危险信号都应优先处理。"],
        "match": {
            "scoreLevels": ["priority"],
            "signalKeywords": ["高关注", "异常", "呼吸困难", "言语", "胸痛"],
            "lifestyleFlags": [],
        },
        "sources": [
            {
                "name": "NIDCD Taking Care of Your Voice",
                "url": "https://www.nidcd.nih.gov/health/taking-care-your-voice",
            },
            {
                "name": "CDC Managing Stress",
                "url": "https://www.cdc.gov/mental-health/living-with/index.html",
            },
        ],
    },
]


def get_evidence_health_plans(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    if not domain or domain == "all":
        return EVIDENCE_HEALTH_PLANS
    return [plan for plan in EVIDENCE_HEALTH_PLANS if plan.get("domain") == domain]


def get_evidence_health_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    return next((plan for plan in EVIDENCE_HEALTH_PLANS if plan.get("id") == plan_id), None)


def match_evidence_health_plans(
    report: Optional[Dict[str, Any]] = None,
    lifestyle_summary: Optional[Dict[str, Any]] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    report = report or {}
    lifestyle_summary = lifestyle_summary or {}
    score_level = _score_level(report.get("score", report.get("overallScore", 0)))
    signal_text = _signal_text(report)
    lifestyle_flags = set(_lifestyle_flags(lifestyle_summary))

    scored: List[Dict[str, Any]] = []
    for plan in EVIDENCE_HEALTH_PLANS:
        match = plan.get("match", {})
        score = 0
        reasons = []
        if score_level in match.get("scoreLevels", []):
            score += 1
            reasons.append("评分等级匹配")
        for keyword in match.get("signalKeywords", []):
            if keyword and keyword in signal_text:
                score += 2
                reasons.append(f"匹配信号：{keyword}")
                break
        overlap = lifestyle_flags.intersection(set(match.get("lifestyleFlags", [])))
        if overlap:
            score += 3
            reasons.append("生活方式记录匹配")
        if plan["id"] == "urgent_red_flags" and score_level == "priority":
            score += 2

        if score > 0:
            scored.append({
                **plan,
                "matchScore": score,
                "matchReasons": reasons,
            })

    scored.sort(key=lambda item: item["matchScore"], reverse=True)
    return scored[:limit]


def _score_level(value: Any) -> str:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        score = 0
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "good"
    if score >= 70:
        return "watch"
    if score >= 60:
        return "attention"
    return "priority"


def _signal_text(report: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("signals", "riskAssessment", "dimensions", "lowDimensions"):
        for item in report.get(key, []) or []:
            parts.extend([
                str(item.get("name", "")),
                str(item.get("category", "")),
                str(item.get("group", "")),
                str(item.get("reason", "")),
                str(item.get("summary", "")),
            ])
    parts.append(str(report.get("summary", "")))
    return " ".join(parts)


def _lifestyle_flags(summary: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    latest = summary.get("latest") or {}
    if _num(summary.get("avgSleepHours")) and _num(summary.get("avgSleepHours")) < 7:
        flags.append("low_sleep")
    if int(summary.get("exerciseDays") or 0) < 3:
        flags.append("low_exercise")
    if _num(summary.get("avgWaterMl")) and _num(summary.get("avgWaterMl")) < 1500:
        flags.append("low_water")
    if _num(summary.get("avgStressLevel")) >= 4:
        flags.append("high_stress")
    if latest.get("alcohol"):
        flags.append("alcohol")
    if latest.get("spicyOily") or latest.get("lateMeal") or latest.get("alcohol"):
        flags.append("throat_irritants")
        flags.append("high_salt_or_oily")
    if int(summary.get("checkinDays") or 0) < 3:
        flags.append("poor_diet_record")
    return flags


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
