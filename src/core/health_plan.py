"""
Health improvement action plan generator.

The output is for wellness coaching and trend interpretation only. It avoids
diagnosis, treatment instructions, and medication advice.
"""

from typing import Any, Dict, List, Optional

from src.core.evidence_health_plans import match_evidence_health_plans


GUIDELINE_REFERENCES = [
    {
        "name": "WHO physical activity guidance",
        "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
        "use": "成年人规律中等强度运动和力量训练目标",
    },
    {
        "name": "CDC sleep guidance",
        "url": "https://www.cdc.gov/sleep/about/index.html",
        "use": "成年人每晚睡眠时长参考",
    },
    {
        "name": "Dietary Guidelines for Americans 2020-2025",
        "url": "https://www.dietaryguidelines.gov/resources/2020-2025-dietary-guidelines-online-materials",
        "use": "均衡饮食、蔬果、全谷物、蛋白来源、控糖控钠原则",
    },
    {
        "name": "CDC water and healthier drinks",
        "url": "https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/index.html",
        "use": "饮水和减少含糖饮料的健康行为建议",
    },
]


def build_action_plan(
    report: Optional[Dict[str, Any]] = None,
    lifestyle_summary: Optional[Dict[str, Any]] = None,
    timeline: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a structured, product-facing action plan."""
    report = report or {}
    lifestyle_summary = lifestyle_summary or {}
    timeline = timeline or []

    score = _num(report.get("score", report.get("overallScore", 0)))
    score_level = _score_level(score)
    latest_lifestyle = lifestyle_summary.get("latest") or {}
    signals = _extract_problem_signals(report)
    low_dimensions = _extract_low_dimensions(report)

    actions: List[Dict[str, Any]] = []
    goals: List[Dict[str, Any]] = []
    red_flags = _red_flags()

    _add_score_goals(goals, score)
    _add_recording_action(actions, report)
    _add_signal_actions(actions, signals)
    _add_dimension_actions(actions, low_dimensions)
    _add_lifestyle_actions(actions, lifestyle_summary, latest_lifestyle)

    if score < 70 or signals:
        _add_unique_action(actions, {
            "id": "recheck_baseline",
            "category": "复测",
            "priority": "high" if score < 60 else "medium",
            "title": "用7天建立可比较的个人基线",
            "why": "单次分数容易受环境、设备、睡眠、压力、饮食和运动影响，连续趋势比单次结果更可靠。",
            "steps": [
                "选择固定时间段，尽量在相同房间和相同手机距离下录制。",
                "连续7天记录语音，并同步填写饮食、运动、睡眠和压力。",
                "若同一维度连续3次下降，再结合身体感受判断是否需要线下评估。",
            ],
            "target": "7天内完成至少5次可比复测",
        })

    if score >= 80 and not signals:
        _add_unique_action(actions, {
            "id": "maintain_routine",
            "category": "维持",
            "priority": "low",
            "title": "维持当前生活方式并保留趋势记录",
            "why": "当前分数较平稳，重点是保持规律习惯并捕捉未来变化。",
            "steps": [
                "每周复测2到3次，不需要每天反复测同一指标。",
                "继续记录睡眠、运动和饮食，形成个人长期基线。",
                "出现感冒、熬夜、饮酒或高强度用嗓时，在备注里记录原因。",
            ],
            "target": "保持4周趋势稳定",
        })

    actions = _sort_actions(actions)[:8]
    evidence_plans = match_evidence_health_plans(report, lifestyle_summary, limit=6)
    return {
        "schemaVersion": "vh.action_plan.v1",
        "positioning": "health_reference",
        "scoreStatus": {
            "score": score,
            "level": score_level["level"],
            "label": score_level["label"],
            "message": score_level["message"],
        },
        "problemSignals": signals[:6],
        "lowDimensions": low_dimensions[:6],
        "evidencePlans": evidence_plans,
        "goals": goals,
        "actions": actions,
        "recheckPlan": {
            "title": "复测节奏",
            "items": [
                "评分低于70分时，建议在相同环境下连续复测3到7天。",
                "评分恢复稳定后，每周2到3次即可。",
                "复测时同步记录饮食、运动、睡眠、压力和症状，便于解释分数波动。",
            ],
        },
        "whenToSeekCare": red_flags,
        "evidence": GUIDELINE_REFERENCES,
        "timelineSummary": _timeline_summary(timeline),
        "notice": "本方案用于健康管理参考，不替代医生诊断、治疗或急症处理。",
    }


def _num(value: Any, default: float = 0) -> float:
    try:
        return round(float(value or default), 1)
    except (TypeError, ValueError):
        return default


def _score_level(score: float) -> Dict[str, str]:
    if score >= 90:
        return {
            "level": "excellent",
            "label": "状态优秀",
            "message": "当前分数较高，重点是保持规律生活和趋势记录。",
        }
    if score >= 80:
        return {
            "level": "good",
            "label": "状态良好",
            "message": "整体平稳，可继续观察睡眠、运动和压力对分数的影响。",
        }
    if score >= 70:
        return {
            "level": "watch",
            "label": "建议观察",
            "message": "部分指标需要关注，优先从睡眠、饮水、运动和复测稳定性改善。",
        }
    if score >= 60:
        return {
            "level": "attention",
            "label": "需要关注",
            "message": "分数偏低，建议连续复测并执行短期恢复计划。",
        }
    return {
        "level": "priority",
        "label": "优先处理",
        "message": "多项指标偏低，请先排查采集质量、近期身体状态和明显不适。",
    }


def _extract_problem_signals(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_signals = report.get("signals") or report.get("riskAssessment") or []
    result: List[Dict[str, Any]] = []
    for item in raw_signals:
        score = _num(item.get("score"))
        level = item.get("level") or ("high" if score >= 72 else "medium" if score >= 45 else "low")
        if level == "low" and score < 45:
            continue
        result.append({
            "id": item.get("id", ""),
            "name": item.get("name", "健康信号"),
            "category": item.get("category") or item.get("group") or "",
            "level": level,
            "score": score,
            "reason": item.get("desc") or item.get("description") or item.get("suggestion") or "",
        })
    return sorted(result, key=lambda item: item["score"], reverse=True)


def _extract_low_dimensions(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_dimensions = report.get("dimensions") or []
    result = []
    for item in raw_dimensions:
        score = _num(item.get("score"))
        if score and score < 75:
            result.append({
                "name": item.get("name", "健康维度"),
                "score": score,
                "level": item.get("level") or ("需关注" if score < 68 else "可观察"),
            })
    return sorted(result, key=lambda item: item["score"])


def _add_score_goals(goals: List[Dict[str, Any]], score: float) -> None:
    if score < 70:
        goals.extend([
            {
                "id": "stabilize_score",
                "title": "先让分数稳定",
                "target": "未来7天在相同条件下复测，观察是否回到70分以上",
                "windowDays": 7,
            },
            {
                "id": "reduce_load",
                "title": "降低近期负荷",
                "target": "连续3天优先保证睡眠、补水、减少刺激性饮食和高强度用嗓",
                "windowDays": 3,
            },
        ])
    else:
        goals.append({
            "id": "maintain_trend",
            "title": "维持健康趋势",
            "target": "未来4周保持每周2到3次记录，观察趋势而不是单次分数",
            "windowDays": 28,
        })


def _add_recording_action(actions: List[Dict[str, Any]], report: Dict[str, Any]) -> None:
    quality = report.get("quality") or {}
    signal_quality = _num(quality.get("signal_quality", quality.get("signalQuality", 0)))
    duration = _num(quality.get("duration", 0))
    if signal_quality and signal_quality < 70 or duration and duration < 20:
        _add_unique_action(actions, {
            "id": "improve_recording_quality",
            "category": "采集质量",
            "priority": "high",
            "title": "先排除录音质量导致的低分",
            "why": "录音时长不足、背景噪声或距离不稳定，会直接影响声学特征和评分。",
            "steps": [
                "选择安静室内，手机麦克风距口部约15到25厘米。",
                "自然语速朗读，尽量录制接近30秒。",
                "避免刚运动、饮酒、哭笑、感冒发热或长时间用嗓后马上录制。",
            ],
            "target": "下一次录音时长达到20秒以上，信号质量高于70分",
        })


def _add_signal_actions(actions: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> None:
    categories = " ".join(item.get("category", "") + " " + item.get("name", "") for item in signals)
    if any(word in categories for word in ("呼吸", "气道", "气短", "心肺")):
        _add_unique_action(actions, {
            "id": "breathing_recovery",
            "category": "呼吸与心肺",
            "priority": "high",
            "title": "观察呼吸耐量并降低短期负荷",
            "why": "气息、停顿和发声占比异常时，近期疲劳、感染、运动负荷或呼吸状态都可能影响分数。",
            "steps": [
                "未来3天避免在剧烈运动后立即录音。",
                "记录爬楼、快走后的气短程度，以及咳嗽、喘息、胸闷情况。",
                "若没有不适，可从10到20分钟轻中等强度步行开始恢复。",
            ],
            "target": "3到7天内观察停顿和气息相关分数是否回升",
        })
    if any(word in categories for word in ("嗓音", "喉", "嘶哑", "反流", "干燥")):
        _add_unique_action(actions, {
            "id": "voice_care",
            "category": "嗓音保护",
            "priority": "high",
            "title": "执行嗓音保护和咽喉刺激控制",
            "why": "嘶哑、气声、干涩或反流相关线索常受用嗓强度、补水、酒精、辛辣油腻和睡前进食影响。",
            "steps": [
                "连续3天减少长时间讲话、喊叫和清嗓。",
                "把饮水记录提高到可持续水平；如医生限制饮水，以医嘱为准。",
                "减少饮酒、辛辣油腻和睡前进食，观察咽喉干涩和声音疲劳变化。",
            ],
            "target": "3天后复测嗓音稳定性和咽喉不适变化",
        })
    if any(word in categories for word in ("睡眠", "疲劳", "活力")):
        _add_unique_action(actions, {
            "id": "sleep_recovery",
            "category": "睡眠恢复",
            "priority": "high",
            "title": "优先恢复睡眠和日间精力",
            "why": "睡眠不足和疲劳可影响语速、停顿、能量和音质稳定性。",
            "steps": [
                "连续7天记录睡眠时长、入睡时间和日间困倦。",
                "尽量固定起床时间，下午或晚间减少咖啡因摄入。",
                "睡前减少长时间屏幕刺激和高强度工作。",
            ],
            "target": "未来7天平均睡眠接近7小时或以上",
        })
    if any(word in categories for word in ("压力", "情绪", "倦怠", "心理")):
        _add_unique_action(actions, {
            "id": "stress_reset",
            "category": "压力管理",
            "priority": "medium",
            "title": "记录压力来源并安排短恢复窗口",
            "why": "压力和倦怠会影响韵律、语速、能量变化和主观疲劳。",
            "steps": [
                "每天给压力打0到5分，并记录主要压力来源。",
                "安排10分钟步行、呼吸放松或离屏休息。",
                "若持续低落、焦虑、兴趣下降或睡眠明显受影响，建议寻求专业帮助。",
            ],
            "target": "7天内观察压力评分和声音能量是否改善",
        })


def _add_dimension_actions(actions: List[Dict[str, Any]], dimensions: List[Dict[str, Any]]) -> None:
    names = " ".join(item.get("name", "") for item in dimensions)
    if "代谢" in names or "衰老" in names:
        _add_unique_action(actions, {
            "id": "nutrition_activity_base",
            "category": "饮食运动",
            "priority": "medium",
            "title": "建立饮食和活动基础",
            "why": "代谢、活力和衰老相关维度需要结合长期饮食、运动、睡眠和压力趋势观察。",
            "steps": [
                "每餐尽量包含优质蛋白、蔬菜或水果，并减少高糖饮料。",
                "从可坚持的步行或低冲击运动开始，逐步增加总量。",
                "每周回顾一次饮食标签和运动分钟数。",
            ],
            "target": "2周内形成至少10天完整生活方式记录",
        })


def _add_lifestyle_actions(
    actions: List[Dict[str, Any]],
    summary: Dict[str, Any],
    latest: Dict[str, Any],
) -> None:
    if _num(summary.get("avgSleepHours")) and _num(summary.get("avgSleepHours")) < 7:
        _add_unique_action(actions, {
            "id": "sleep_hours_target",
            "category": "睡眠",
            "priority": "high",
            "title": "把睡眠作为第一优先级",
            "why": "近期平均睡眠低于成年人常用参考目标，可能影响疲劳、声音能量和压力恢复。",
            "steps": [
                "未来7天记录睡眠小时数和起床精神状态。",
                "先把目标设为比当前平均值增加30到60分钟。",
                "若长期失眠、白天明显嗜睡或打鼾憋醒，建议咨询专业医生。",
            ],
            "target": "7天平均睡眠逐步接近7小时",
        })

    if int(summary.get("exerciseDays") or 0) < 3:
        _add_unique_action(actions, {
            "id": "exercise_minimum",
            "category": "运动",
            "priority": "medium",
            "title": "从低门槛运动开始提高活力",
            "why": "规律身体活动有助于心肺活力、压力管理和睡眠质量。",
            "steps": [
                "本周先完成3次10到20分钟步行或等量低强度活动。",
                "能轻松完成后，再逐步增加到每周150分钟左右中等强度活动。",
                "每周加入2次简单力量训练或抗阻练习，量力而行。",
            ],
            "target": "本周至少3天有运动记录",
        })

    if _num(summary.get("avgWaterMl")) and _num(summary.get("avgWaterMl")) < 1500:
        _add_unique_action(actions, {
            "id": "hydration_target",
            "category": "饮水",
            "priority": "medium",
            "title": "提高饮水记录的稳定性",
            "why": "饮水不足可能加重咽喉干涩和声音疲劳，尤其在长时间讲话或运动后。",
            "steps": [
                "把饮水分散到上午、下午和晚饭前，避免一次性大量补水。",
                "减少含糖饮料，把白水或无糖饮品作为主要来源。",
                "如有心肾疾病或医生限制饮水，以医嘱为准。",
            ],
            "target": "未来7天记录饮水量，并观察咽干变化",
        })

    if _num(summary.get("avgStressLevel")) >= 4:
        _add_unique_action(actions, {
            "id": "stress_level_high",
            "category": "压力",
            "priority": "high",
            "title": "降低高压力对声音和恢复的影响",
            "why": "近期压力评分偏高，可能影响语速、韵律、睡眠和恢复。",
            "steps": [
                "每天记录压力来源，不只记录分数。",
                "安排一个固定的10分钟恢复窗口，例如散步、拉伸或离屏休息。",
                "如果压力伴随持续失眠、明显焦虑或低落，建议寻求专业支持。",
            ],
            "target": "7天内把平均压力评分降低1分或以上",
        })

    if latest.get("alcohol") or latest.get("spicyOily") or latest.get("lateMeal"):
        _add_unique_action(actions, {
            "id": "throat_irritants",
            "category": "饮食",
            "priority": "medium",
            "title": "减少咽喉刺激因素",
            "why": "饮酒、辛辣油腻和睡前进食可能影响咽喉不适、反流刺激和嗓音稳定性。",
            "steps": [
                "连续3天减少酒精、辛辣油腻和睡前进食。",
                "同步记录咽干、清嗓、嘶哑和睡醒后的嗓音状态。",
                "若反复咽喉不适或持续嘶哑超过两周，建议耳鼻喉评估。",
            ],
            "target": "3天后对比嗓音和咽喉症状",
        })


def _add_unique_action(actions: List[Dict[str, Any]], action: Dict[str, Any]) -> None:
    if not any(item.get("id") == action.get("id") for item in actions):
        actions.append(action)


def _sort_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(actions, key=lambda item: order.get(item.get("priority"), 3))


def _timeline_summary(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores = [_num(item.get("score")) for item in timeline if _num(item.get("score")) > 0]
    if not scores:
        return {"count": 0, "direction": "unknown", "message": "暂无足够趋势数据。"}
    direction = "stable"
    if len(scores) >= 2:
        diff = scores[-1] - scores[0]
        if diff >= 5:
            direction = "up"
        elif diff <= -5:
            direction = "down"
    messages = {
        "up": "近期评分有回升迹象，建议保持当前改善动作。",
        "down": "近期评分有下降迹象，建议优先复查采集质量和生活方式变化。",
        "stable": "近期评分相对平稳，继续观察即可。",
    }
    return {
        "count": len(scores),
        "direction": direction,
        "firstScore": scores[0],
        "latestScore": scores[-1],
        "message": messages.get(direction, "暂无足够趋势数据。"),
    }


def _red_flags() -> List[str]:
    return [
        "胸痛、明显气促、喘憋、嘴唇发紫等急性症状，应立即就医。",
        "突然言语含糊、口角歪斜、肢体无力或意识异常，应立即就医。",
        "持续嘶哑超过两周、吞咽困难、咽喉疼痛或咳血，建议耳鼻喉评估。",
        "持续低落、焦虑、失眠或有自伤想法，应尽快寻求专业帮助。",
    ]
