"""
声音大健康风险提示模型

基于可解释声学特征输出健康参考维度。这里不是医学诊断模型；在没有
经过本地临床验证和监管审批前，所有结论都只能作为健康管理提示。
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List


DISEASE_REGISTRY = {
    "respiratory_control": {"name": "呼吸控制能力", "category": "呼吸与气道", "markers": ["pause_ratio", "speech_rate", "voiced_ratio"], "description": "朗读时气息连续性、停顿和发声稳定性"},
    "breath_shortness": {"name": "气短/气息不足线索", "category": "呼吸与气道", "markers": ["pause_ratio", "avg_pause_duration", "rms_mean"], "description": "语音中短句、频繁停顿和能量不足的组合"},
    "airway_irritation": {"name": "气道刺激线索", "category": "呼吸与气道", "markers": ["spectral_flatness", "zcr", "hnr"], "description": "粗糙、噪声化发声和清嗓样声学变化"},
    "sleep_apnea_proxy": {"name": "睡眠呼吸风险代理", "category": "呼吸与气道", "markers": ["pause_pattern", "breathiness", "voice_activity"], "description": "仅基于朗读气息与停顿的睡眠呼吸风险提示"},
    "vocal_hoarseness": {"name": "声音嘶哑/音质粗糙", "category": "嗓音与喉部", "markers": ["jitter", "shimmer", "hnr"], "description": "声带振动稳定性和谐噪比变化"},
    "vocal_fatigue": {"name": "声带疲劳", "category": "嗓音与喉部", "markers": ["rms", "hnr", "prosody"], "description": "音量、音质和韵律活力下降"},
    "throat_dryness": {"name": "咽喉干燥线索", "category": "嗓音与喉部", "markers": ["flatness", "hnr", "hoarseness"], "description": "干涩、毛刺感相关的声学粗糙度"},
    "reflux_irritation": {"name": "反流/咽喉刺激线索", "category": "嗓音与喉部", "markers": ["hoarseness", "low_hnr"], "description": "长期喉部刺激可能导致的音质变化"},
    "parkinsonian_voice": {"name": "帕金森样发声线索", "category": "神经运动", "markers": ["jitter", "shimmer", "f0_variability"], "description": "微弱、单调、震颤样发声特征"},
    "speech_motor_control": {"name": "构音运动控制", "category": "神经运动", "markers": ["articulation", "spectral_flux", "speech_rate"], "description": "发音清晰度、音节转换和节律稳定性"},
    "tremor_stability": {"name": "声带震颤稳定性", "category": "神经运动", "markers": ["f0_std", "jitter"], "description": "基频微扰和异常波动"},
    "neurological_fatigue": {"name": "神经疲劳线索", "category": "神经运动", "markers": ["energy", "pause", "prosody"], "description": "发声驱动力和韵律活力下降"},
    "depressive_voice": {"name": "低落情绪语音线索", "category": "心理与压力", "markers": ["speech_rate", "pause", "f0_variability"], "description": "语速变慢、停顿增加、韵律变平"},
    "anxiety_tension": {"name": "焦虑/紧张语音线索", "category": "心理与压力", "markers": ["pitch", "speech_rate", "zcr"], "description": "音高升高、语速加快和高频紧张度"},
    "stress_load": {"name": "压力负荷", "category": "心理与压力", "markers": ["pitch_variability", "energy_variation"], "description": "韵律波动、能量起伏和语速异常"},
    "burnout_risk": {"name": "倦怠风险线索", "category": "心理与压力", "markers": ["fatigue", "stress", "flat_prosody"], "description": "疲劳与压力信号同时升高"},
    "sleep_debt": {"name": "睡眠不足线索", "category": "睡眠与疲劳", "markers": ["rms", "pause", "hoarseness"], "description": "声音疲劳、能量不足和反应迟缓"},
    "daytime_fatigue": {"name": "日间疲劳", "category": "睡眠与疲劳", "markers": ["energy", "speech_rate", "voice_activity"], "description": "朗读活力和持续发声能力下降"},
    "recovery_vitality": {"name": "恢复活力", "category": "睡眠与疲劳", "markers": ["volume_stability", "prosody", "signal_quality"], "description": "声音活力、韵律和稳定性综合参考"},
    "cognitive_load": {"name": "认知负荷", "category": "认知与沟通", "markers": ["pause", "speech_rate", "articulation"], "description": "停顿、节律和表达流畅度变化"},
    "attention_fluency": {"name": "注意与流畅度", "category": "认知与沟通", "markers": ["pause_count", "spectral_flux"], "description": "连续朗读中的流畅程度和转换效率"},
    "emotional_flatness": {"name": "情感韵律平坦", "category": "认知与沟通", "markers": ["f0_std", "rms_std"], "description": "音高和响度表达范围降低"},
    "cardiopulmonary_load": {"name": "心肺负荷线索", "category": "心肺活力", "markers": ["breath_control", "energy", "pause"], "description": "心肺耐受力相关的发声持续性代理指标"},
    "frailty_vitality": {"name": "衰弱/活力下降线索", "category": "总体活力", "markers": ["speech_rate", "energy", "voice_activity"], "description": "语速、音量和持续发声能力的综合活力提示"},
    "voice_ageing": {"name": "声音老化线索", "category": "总体活力", "markers": ["jitter", "shimmer", "hnr", "prosody"], "description": "音质稳定性、谐噪比和韵律范围变化"}
}


@dataclass
class HealthReport:
    overall_score: float = 75.0
    summary: str = ""
    risks: List[Dict] = field(default_factory=list)
    features: List[Dict] = field(default_factory=list)
    domains: List[Dict] = field(default_factory=list)
    voice_quality: Dict = field(default_factory=dict)
    ai_insight: str = ""

    def to_dict(self):
        return {
            "overall_score": self.overall_score,
            "summary": self.summary,
            "risks": self.risks,
            "features": self.features,
            "domains": self.domains,
            "voice_quality": self.voice_quality,
            "ai_insight": self.ai_insight,
        }


class DiseaseDetector:
    def generate_report(self, features) -> HealthReport:
        risk_items = self._risk_items(features)
        domains = self._domain_scores(risk_items)
        overall_risk = sum(item["score"] for item in risk_items) / max(len(risk_items), 1)
        overall_score = round(self._clamp(100 - overall_risk * 0.72), 1)
        top_risks = sorted(risk_items, key=lambda item: item["score"], reverse=True)[:3]

        return HealthReport(
            overall_score=overall_score,
            summary=self._summary(overall_score, top_risks),
            risks=risk_items,
            features=self._feature_cards(features),
            domains=domains,
            voice_quality=self._quality(features),
            ai_insight=self._insight(top_risks, overall_score)
        )

    def _risk_items(self, f) -> List[Dict]:
        calculators: Dict[str, Callable] = {
            "respiratory_control": lambda: self._mix(self._pause_risk(f), self._slow_rate(f), self._low_voicing(f), weights=(0.45, 0.25, 0.30)),
            "breath_shortness": lambda: self._mix(self._pause_risk(f), self._low_energy(f), self._risk_high(f.avg_pause_duration, 0.6, 1.8), weights=(0.45, 0.35, 0.20)),
            "airway_irritation": lambda: self._mix(self._risk_high(f.spectral_flatness_mean, 0.08, 0.35), self._risk_low(f.hnr_mean, 18, 5), self._risk_high(f.zcr_mean, 0.16, 0.35)),
            "sleep_apnea_proxy": lambda: self._mix(self._pause_risk(f), self._risk_high(f.avg_pause_duration, 0.7, 2.0), self._risk_low(f.voice_activity_ratio, 0.65, 0.25)),
            "vocal_hoarseness": lambda: self._mix(self._risk_high(f.hoarseness_index, 30, 80), self._risk_low(f.hnr_mean, 20, 6)),
            "vocal_fatigue": lambda: self._mix(self._low_energy(f), self._risk_low(f.prosody_variability, 12, 2), self._risk_low(f.volume_stability, 70, 25)),
            "throat_dryness": lambda: self._mix(self._risk_high(f.breathiness_index, 28, 78), self._risk_high(f.spectral_flatness_mean, 0.10, 0.35)),
            "reflux_irritation": lambda: self._mix(self._risk_high(f.hoarseness_index, 35, 80), self._risk_low(f.hnr_mean, 18, 4), weights=(0.65, 0.35)),
            "parkinsonian_voice": lambda: self._mix(self._risk_high(f.jitter_local, 0.018, 0.08), self._risk_high(f.shimmer_local, 0.10, 0.35), self._risk_low(f.prosody_variability, 10, 2)),
            "speech_motor_control": lambda: self._risk_low(f.articulation_stability, 76, 35),
            "tremor_stability": lambda: self._mix(self._risk_high(f.jitter_local, 0.02, 0.08), self._risk_high(f.f0_std, 45, 120), weights=(0.65, 0.35)),
            "neurological_fatigue": lambda: self._mix(self._low_energy(f), self._pause_risk(f), self._risk_low(f.prosody_variability, 11, 2)),
            "depressive_voice": lambda: self._mix(self._slow_rate(f), self._pause_risk(f), self._risk_low(f.prosody_variability, 12, 2), self._low_energy(f), weights=(0.30, 0.30, 0.25, 0.15)),
            "anxiety_tension": lambda: self._mix(self._fast_rate(f), self._risk_high(f.prosody_variability, 35, 85), self._risk_high(f.zcr_mean, 0.14, 0.32)),
            "stress_load": lambda: self._mix(self._risk_outside(f.speech_rate, 2.2, 7.2, 3.0), self._risk_high(f.prosody_variability, 32, 80), self._risk_low(f.volume_stability, 65, 25)),
            "burnout_risk": lambda: self._mix(self._low_energy(f), self._pause_risk(f), self._risk_high(f.hoarseness_index, 35, 80)),
            "sleep_debt": lambda: self._mix(self._low_energy(f), self._slow_rate(f), self._risk_high(f.hoarseness_index, 30, 80)),
            "daytime_fatigue": lambda: self._mix(self._low_energy(f), self._risk_low(f.voice_activity_ratio, 0.68, 0.30), self._slow_rate(f)),
            "recovery_vitality": lambda: self._mix(self._risk_low(f.volume_stability, 72, 30), self._risk_low(f.prosody_variability, 12, 2), self._risk_low(f.signal_quality, 72, 25)),
            "cognitive_load": lambda: self._mix(self._pause_risk(f), self._risk_outside(f.speech_rate, 2.0, 7.4, 3.0), self._risk_low(f.articulation_stability, 76, 35)),
            "attention_fluency": lambda: self._mix(self._risk_high(f.pause_count / max(f.total_duration, 1), 0.25, 1.4), self._risk_low(f.spectral_flux_std, 0.10, 0.02), self._risk_low(f.articulation_stability, 74, 35)),
            "emotional_flatness": lambda: self._mix(self._risk_low(f.prosody_variability, 12, 2), self._risk_low(f.rms_std, 0.035, 0.005), weights=(0.70, 0.30)),
            "cardiopulmonary_load": lambda: self._mix(self._pause_risk(f), self._low_energy(f), self._risk_low(f.voice_activity_ratio, 0.65, 0.25)),
            "frailty_vitality": lambda: self._mix(self._slow_rate(f), self._low_energy(f), self._risk_low(f.voice_activity_ratio, 0.65, 0.25), self._risk_low(f.articulation_stability, 72, 35)),
            "voice_ageing": lambda: self._mix(self._risk_high(f.jitter_local, 0.018, 0.08), self._risk_high(f.shimmer_local, 0.10, 0.35), self._risk_low(f.hnr_mean, 19, 5), self._risk_low(f.prosody_variability, 12, 2)),
        }

        items = []
        for key, meta in DISEASE_REGISTRY.items():
            score = round(self._clamp(calculators[key]()), 1)
            level, level_text = self._level(score)
            items.append({
                "id": key,
                "name": meta["name"],
                "category": meta["category"],
                "level": level,
                "levelText": level_text,
                "score": score,
                "description": meta["description"],
                "suggestion": self._suggestion(key, level),
                "markers": meta["markers"],
            })
        return items

    def _feature_cards(self, f) -> List[Dict]:
        return [
            self._feature("录音时长", f"{f.total_duration:.1f}s", self._health_low(f.total_duration, 20, 5), "建议录制接近30秒以提高稳定性"),
            self._feature("语速", f"{f.speech_rate:.1f}/s", 100 - self._risk_outside(f.speech_rate, 2.0, 7.5, 3.0), "语速反映节律、疲劳和流畅度"),
            self._feature("停顿比例", f"{f.pause_ratio * 100:.0f}%", 100 - self._pause_risk(f), "停顿过多可能影响呼吸和认知负荷判断"),
            self._feature("声音活动", f"{f.voice_activity_ratio * 100:.0f}%", self._health_low(f.voice_activity_ratio, 0.65, 0.25), "持续发声能力参考"),
            self._feature("平均音高", f"{f.f0_mean:.0f}Hz", 100 - self._risk_outside(f.f0_mean, 85, 260, 120), "个体差异较大，主要看趋势变化"),
            self._feature("音高波动", f"{f.prosody_variability:.1f}%", 100 - self._risk_outside(f.prosody_variability, 6, 35, 30), "反映情绪韵律和表达活力"),
            self._feature("声带抖动", f"{f.jitter_local * 100:.2f}%", 100 - self._risk_high(f.jitter_local, 0.018, 0.08), "声带振动微扰指标"),
            self._feature("振幅扰动", f"{f.shimmer_local * 100:.1f}%", 100 - self._risk_high(f.shimmer_local, 0.10, 0.35), "响度稳定性参考"),
            self._feature("谐噪比", f"{f.hnr_mean:.1f}dB", self._health_low(f.hnr_mean, 20, 5), "越高通常代表音质越清晰"),
            self._feature("发音清晰度", f"{f.articulation_stability:.0f}", f.articulation_stability, "基于频谱变化、语速和停顿的综合指标"),
            self._feature("音量稳定", f"{f.volume_stability:.0f}", f.volume_stability, "反映能量起伏是否自然稳定"),
            self._feature("气声指数", f"{f.breathiness_index:.0f}", 100 - f.breathiness_index, "气声偏高可能提示漏气或嗓音疲劳"),
            self._feature("嘶哑指数", f"{f.hoarseness_index:.0f}", 100 - f.hoarseness_index, "综合抖动、扰动和谐噪比"),
            self._feature("频谱重心", f"{f.spectral_centroid_mean:.0f}Hz", 100 - self._risk_outside(f.spectral_centroid_mean, 900, 3600, 1800), "反映声音明亮度"),
            self._feature("过零率", f"{f.zcr_mean:.3f}", 100 - self._risk_outside(f.zcr_mean, 0.02, 0.22, 0.18), "反映清浊音与噪声成分"),
            self._feature("信号质量", f"{f.signal_quality:.0f}", f.signal_quality, "受环境噪声、削波和录音时长影响"),
        ]

    def _domain_scores(self, risks: List[Dict]) -> List[Dict]:
        groups: Dict[str, List[float]] = {}
        for item in risks:
            groups.setdefault(item["category"], []).append(item["score"])

        domains = []
        for name, values in groups.items():
            risk = sum(values) / len(values)
            score = round(self._clamp(100 - risk), 1)
            domains.append({
                "name": name,
                "score": score,
                "level": self._domain_level(score),
                "desc": f"包含 {len(values)} 项声音健康参考指标"
            })
        return sorted(domains, key=lambda item: item["score"])

    def _quality(self, f) -> Dict:
        return {
            "signal_quality": round(f.signal_quality, 1),
            "liveness_ready": f.total_duration >= 5 and f.signal_quality >= 35,
            "duration": round(f.total_duration, 1),
            "snr_estimate": round(f.snr_estimate, 1),
            "clipping_ratio": round(f.clipping_ratio, 4),
            "voice_activity_ratio": round(f.voice_activity_ratio, 3),
        }

    def _summary(self, score: float, top_risks: List[Dict]) -> str:
        if score >= 85:
            base = "本次声音大健康参考显示整体状态较好。"
        elif score >= 75:
            base = "本次声音参考整体平稳，少数维度建议持续观察。"
        elif score >= 65:
            base = "本次声音参考提示存在若干需要关注的健康管理信号。"
        else:
            base = "本次声音参考提示多项指标偏低，建议结合复测和线下评估。"

        if not top_risks:
            return base
        names = "、".join(item["name"] for item in top_risks[:2])
        return f"{base} 相对突出的维度为：{names}。"

    def _insight(self, top_risks: List[Dict], score: float) -> str:
        suggestions = [item["suggestion"] for item in top_risks if item.get("suggestion")]
        if score < 70:
            suggestions.append("如近期伴随不适、睡眠明显下降或呼吸困难，请及时咨询专业医生。")
        suggestions.append("建议在相同时间段、相似环境下连续复测，重点观察趋势而非单次分数。")
        return " ".join(dict.fromkeys(suggestions))

    @staticmethod
    def _feature(name: str, value: str, percent: float, desc: str) -> Dict:
        return {
            "name": name,
            "value": value,
            "percent": int(max(0, min(100, round(percent)))),
            "desc": desc
        }

    @staticmethod
    def _level(score: float):
        if score >= 72:
            return "high", "高关注"
        if score >= 45:
            return "medium", "中等关注"
        return "low", "低关注"

    @staticmethod
    def _domain_level(score: float) -> str:
        if score >= 82:
            return "良好"
        if score >= 68:
            return "可观察"
        return "需关注"

    @staticmethod
    def _suggestion(key: str, level: str) -> str:
        common = {
            "respiratory_control": "保持自然语速朗读；若长期气短或胸闷，应咨询医生。",
            "breath_shortness": "关注运动耐量和呼吸状态，避免在剧烈运动后立即采集。",
            "airway_irritation": "补充水分，减少烟酒和刺激性环境暴露。",
            "sleep_apnea_proxy": "若存在打鼾、白天嗜睡或憋醒，请考虑睡眠医学评估。",
            "vocal_hoarseness": "减少连续高强度用嗓，持续嘶哑超过两周建议就医。",
            "vocal_fatigue": "安排声音休息，避免长时间大声说话。",
            "throat_dryness": "增加饮水，保持环境湿度。",
            "reflux_irritation": "避免睡前进食和刺激性饮食，反复咽喉不适建议就医。",
            "parkinsonian_voice": "若伴随手抖、动作变慢或步态异常，应咨询神经科。",
            "speech_motor_control": "观察发音含混、吞咽或面部运动变化。",
            "tremor_stability": "建议复测并关注是否存在持续性声音震颤。",
            "neurological_fatigue": "保证睡眠和恢复，必要时结合神经系统症状评估。",
            "depressive_voice": "关注情绪、兴趣和睡眠变化，持续低落建议寻求专业帮助。",
            "anxiety_tension": "尝试呼吸放松训练，避免在强紧张状态下采集。",
            "stress_load": "记录压力来源，结合心率、睡眠和主观压力综合判断。",
            "burnout_risk": "降低连续工作负荷，优先恢复睡眠和运动。",
            "sleep_debt": "优先保证规律睡眠，连续异常建议复测。",
            "daytime_fatigue": "关注日间困倦、咖啡因依赖和运动恢复。",
            "recovery_vitality": "保持规律运动和恢复，观察趋势改善。",
            "cognitive_load": "在安静环境复测，关注近期注意力和工作负荷。",
            "attention_fluency": "若持续出现明显表达卡顿，建议结合认知评估。",
            "emotional_flatness": "关注情绪表达、社交兴趣和疲劳状态。",
            "cardiopulmonary_load": "若伴随胸闷、气促、下肢水肿等症状，请及时就医。",
            "frailty_vitality": "增加蛋白摄入和抗阻训练，关注体重和体力变化。",
            "voice_ageing": "以长期趋势为主，结合运动、睡眠和慢病管理综合改善。"
        }
        if level == "low":
            return "当前为低关注，建议作为长期趋势参考。"
        return common.get(key, "建议结合生活方式和复测趋势进行健康管理。")

    def _pause_risk(self, f) -> float:
        return self._risk_high(f.pause_ratio, 0.20, 0.55)

    def _slow_rate(self, f) -> float:
        return self._risk_low(f.speech_rate, 3.0, 0.8)

    def _fast_rate(self, f) -> float:
        return self._risk_high(f.speech_rate, 6.5, 10.0)

    def _low_energy(self, f) -> float:
        return self._risk_low(f.rms_mean, 0.045, 0.006)

    def _low_voicing(self, f) -> float:
        return self._risk_low(f.voiced_ratio or f.voice_activity_ratio, 0.62, 0.22)

    def _health_low(self, value: float, good: float, poor: float) -> float:
        return 100 - self._risk_low(value, good, poor)

    @staticmethod
    def _mix(*values, weights=None) -> float:
        if not values:
            return 0.0
        if not weights:
            weights = [1 / len(values)] * len(values)
        total_weight = sum(weights) or 1
        return sum(value * weight for value, weight in zip(values, weights)) / total_weight

    @staticmethod
    def _risk_high(value: float, start: float, end: float) -> float:
        if value <= start:
            return 0.0
        if value >= end:
            return 100.0
        return (value - start) / (end - start) * 100

    @staticmethod
    def _risk_low(value: float, good: float, poor: float) -> float:
        if value >= good:
            return 0.0
        if value <= poor:
            return 100.0
        return (good - value) / (good - poor) * 100

    def _risk_outside(self, value: float, low: float, high: float, span: float) -> float:
        if low <= value <= high:
            return 0.0
        if value < low:
            return self._risk_low(value, low, low - span)
        return self._risk_high(value, high, high + span)

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, value))
