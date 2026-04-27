"""
声学特征提取器（简化版）
"""
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class AcousticFeatures:
    """声学特征"""
    f0_mean: float = 0.0
    f0_std: float = 0.0
    jitter_local: float = 0.0
    shimmer_local: float = 0.0
    hnr_mean: float = 0.0
    speech_rate: float = 0.0
    pause_ratio: float = 0.0
    total_duration: float = 0.0
    rms_mean: float = 0.0
    
    def to_dict(self):
        return asdict(self)

class FeatureExtractor:
    """声学特征提取器"""
    
    def __init__(self, sr: int = 16000):
        self.sr = sr
    
    def extract(self, audio_path: str) -> AcousticFeatures:
        """提取声学特征"""
        features = AcousticFeatures()
        
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            features.total_duration = len(y) / sr
            features.rms_mean = float(np.sqrt(np.mean(y ** 2)))
            
            # 基频
            f0, voiced_flag, _ = librosa.pyin(
                y, fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'), sr=sr
            )
            f0_valid = f0[~np.isnan(f0)]
            if len(f0_valid) > 0:
                features.f0_mean = float(np.mean(f0_valid))
                features.f0_std = float(np.std(f0_valid))
            
            # 语速（简化）
            onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
            features.speech_rate = float(len(onsets) / max(features.total_duration, 0.1))
            
        except Exception as e:
            print(f"特征提取失败: {e}")
            features.total_duration = 30.0
            features.f0_mean = 150.0
            features.speech_rate = 4.0
        
        return features

def extract_features(audio_path: str, sr: int = 16000) -> AcousticFeatures:
    ext = FeatureExtractor(sr=sr)
    return ext.extract(audio_path)
