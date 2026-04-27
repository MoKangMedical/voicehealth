"""
语音验证器（简化版）
"""
from dataclasses import dataclass, field
from typing import Dict, List

READING_TEXTS = [
    {"id": "standard_1", "text": "春天来了，花儿开了，小鸟在枝头唱歌。", "keywords": ["春天", "花儿", "小鸟"]},
    {"id": "standard_2", "text": "健康是人生最宝贵的财富。", "keywords": ["健康", "财富"]},
    {"id": "standard_3", "text": "科技改变了我们的生活。", "keywords": ["科技", "生活"]}
]

@dataclass
class LivenessResult:
    is_live: bool = True
    confidence: float = 0.8
    score: float = 0.8
    checks: Dict[str, bool] = field(default_factory=dict)

class LivenessDetector:
    def __init__(self, sr: int = 16000):
        self.sr = sr
    
    def detect(self, audio_path: str) -> LivenessResult:
        return LivenessResult(is_live=True, score=0.85)

class ReadingVerifier:
    def verify(self, text: str, expected_id: str):
        return {"is_valid": True, "confidence": 0.8}
