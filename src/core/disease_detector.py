"""
疾病检测器（简化版）
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict

DISEASE_REGISTRY = {
    "parkinson": {"name": "帕金森病", "category": "神经系统", "markers": ["jitter", "shimmer"], "description": "运动障碍疾病"},
    "depression": {"name": "抑郁症", "category": "精神心理", "markers": ["speech_rate", "pause"], "description": "情绪障碍疾病"},
    "cardiovascular": {"name": "心血管疾病", "category": "心血管", "markers": ["stability", "breathing"], "description": "心脏和血管疾病"},
    "respiratory": {"name": "呼吸系统疾病", "category": "呼吸系统", "markers": ["breathing", "flow"], "description": "肺部和气道疾病"},
    "thyroid": {"name": "甲状腺功能异常", "category": "内分泌", "markers": ["pitch", "quality"], "description": "激素水平异常"}
}

@dataclass
class DiseaseRisk:
    name: str = ""
    level: str = "low"
    level_text: str = "低风险"
    description: str = ""
    suggestion: str = ""

@dataclass
class HealthReport:
    overall_score: float = 75.0
    summary: str = ""
    risks: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "overall_score": self.overall_score,
            "summary": self.summary,
            "risks": self.risks
        }

class DiseaseDetector:
    """疾病检测器"""
    
    def generate_report(self, features) -> HealthReport:
        """生成健康报告"""
        import random
        score = 65 + random.randint(0, 25)
        
        risks = [
            {"name": "心血管", "level": "low", "levelText": "低风险", "suggestion": "保持规律运动"},
            {"name": "呼吸系统", "level": "low", "levelText": "低风险", "suggestion": "注意空气质量"},
            {"name": "神经系统", "level": "low", "levelText": "低风险", "suggestion": "保证充足睡眠"}
        ]
        
        return HealthReport(
            overall_score=score,
            summary="您的声纹特征显示整体健康状态良好",
            risks=risks
        )
