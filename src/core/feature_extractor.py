"""
声学特征提取器

面向大健康参考报告，提取音高、音质、能量、停顿、频谱、韵律和信号质量等
可解释特征。结果不是医学诊断，只作为后续风险提示的输入。
"""

from dataclasses import asdict, dataclass, field
from typing import List

import numpy as np


@dataclass
class AcousticFeatures:
    f0_mean: float = 0.0
    f0_std: float = 0.0
    f0_min: float = 0.0
    f0_max: float = 0.0
    f0_range: float = 0.0
    voiced_ratio: float = 0.0
    jitter_local: float = 0.0
    shimmer_local: float = 0.0
    hnr_mean: float = 0.0
    speech_rate: float = 0.0
    pause_ratio: float = 0.0
    pause_count: int = 0
    avg_pause_duration: float = 0.0
    total_duration: float = 0.0
    rms_mean: float = 0.0
    rms_std: float = 0.0
    energy_entropy: float = 0.0
    zcr_mean: float = 0.0
    zcr_std: float = 0.0
    spectral_centroid_mean: float = 0.0
    spectral_bandwidth_mean: float = 0.0
    spectral_rolloff_mean: float = 0.0
    spectral_flatness_mean: float = 0.0
    spectral_flux_mean: float = 0.0
    spectral_flux_std: float = 0.0
    mfcc_mean: List[float] = field(default_factory=list)
    mfcc_std: List[float] = field(default_factory=list)
    breathiness_index: float = 0.0
    hoarseness_index: float = 0.0
    articulation_stability: float = 0.0
    prosody_variability: float = 0.0
    volume_stability: float = 0.0
    signal_quality: float = 0.0
    clipping_ratio: float = 0.0
    snr_estimate: float = 0.0
    voice_activity_ratio: float = 0.0

    def to_dict(self):
        return asdict(self)


class FeatureExtractor:
    def __init__(self, sr: int = 16000):
        self.sr = sr

    def extract(self, audio_path: str) -> AcousticFeatures:
        features = AcousticFeatures()

        try:
            import librosa

            y, sr = librosa.load(audio_path, sr=self.sr, mono=True)
            if y.size == 0:
                return self._fallback(features)

            peak = float(np.max(np.abs(y)) or 1.0)
            y_norm = y / peak

            features.total_duration = float(len(y_norm) / sr)
            features.clipping_ratio = float(np.mean(np.abs(y_norm) > 0.98))

            frame_length = int(0.025 * sr)
            hop_length = int(0.010 * sr)

            rms = librosa.feature.rms(
                y=y_norm,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            features.rms_mean = float(np.mean(rms))
            features.rms_std = float(np.std(rms))

            nonzero_rms = rms[rms > max(np.max(rms) * 0.02, 1e-6)]
            if nonzero_rms.size:
                cv = float(np.std(nonzero_rms) / (np.mean(nonzero_rms) + 1e-9))
                features.volume_stability = self._clamp(100 - cv * 45)

            silence_threshold = max(np.max(rms) * 0.05, np.median(rms) * 0.8, 1e-5)
            is_voice = rms >= silence_threshold
            features.voice_activity_ratio = float(np.mean(is_voice)) if rms.size else 0.0
            features.pause_ratio = float(1 - features.voice_activity_ratio)
            features.pause_count, features.avg_pause_duration = self._pause_stats(is_voice, hop_length, sr)

            energy = rms ** 2
            if np.sum(energy) > 0:
                p = energy / (np.sum(energy) + 1e-12)
                features.energy_entropy = float(-np.sum(p * np.log(p + 1e-12)) / np.log(len(p) + 1e-12))

            zcr = librosa.feature.zero_crossing_rate(
                y_norm,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            features.zcr_mean = float(np.mean(zcr))
            features.zcr_std = float(np.std(zcr))

            centroid = librosa.feature.spectral_centroid(y=y_norm, sr=sr, hop_length=hop_length)[0]
            bandwidth = librosa.feature.spectral_bandwidth(y=y_norm, sr=sr, hop_length=hop_length)[0]
            rolloff = librosa.feature.spectral_rolloff(y=y_norm, sr=sr, hop_length=hop_length)[0]
            flatness = librosa.feature.spectral_flatness(y=y_norm, hop_length=hop_length)[0]
            features.spectral_centroid_mean = float(np.mean(centroid))
            features.spectral_bandwidth_mean = float(np.mean(bandwidth))
            features.spectral_rolloff_mean = float(np.mean(rolloff))
            features.spectral_flatness_mean = float(np.mean(flatness))

            onset_times = librosa.onset.onset_detect(y=y_norm, sr=sr, units='time')
            active_duration = max(features.total_duration * max(features.voice_activity_ratio, 0.2), 0.1)
            features.speech_rate = float(len(onset_times) / active_duration)

            f0, _, _ = librosa.pyin(
                y_norm,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr,
                frame_length=max(1024, frame_length * 4),
                hop_length=hop_length
            )
            f0_valid = f0[~np.isnan(f0)]
            if f0_valid.size:
                features.f0_mean = float(np.mean(f0_valid))
                features.f0_std = float(np.std(f0_valid))
                features.f0_min = float(np.min(f0_valid))
                features.f0_max = float(np.max(f0_valid))
                features.f0_range = float(features.f0_max - features.f0_min)
                features.voiced_ratio = float(f0_valid.size / max(len(f0), 1))
                features.prosody_variability = float((features.f0_std / (features.f0_mean + 1e-9)) * 100)
                if f0_valid.size > 2:
                    features.jitter_local = float(np.mean(np.abs(np.diff(f0_valid))) / (features.f0_mean + 1e-9))

            voiced_rms = rms[:len(f0)] if 'f0' in locals() else rms
            if f0_valid.size > 2 and voiced_rms.size > 2:
                voiced_rms = voiced_rms[:len(f0)]
                voiced_rms = voiced_rms[~np.isnan(f0)]
                if voiced_rms.size > 2:
                    features.shimmer_local = float(np.mean(np.abs(np.diff(voiced_rms))) / (np.mean(voiced_rms) + 1e-9))

            stft = np.abs(librosa.stft(y_norm, n_fft=1024, hop_length=hop_length))
            if stft.shape[1] > 2:
                flux = np.sqrt(np.sum(np.diff(stft, axis=1) ** 2, axis=0))
                flux_norm = flux / (np.max(flux) + 1e-9)
                features.spectral_flux_mean = float(np.mean(flux_norm))
                features.spectral_flux_std = float(np.std(flux_norm))

                harmonic, percussive = librosa.decompose.hpss(stft)
                harmonic_energy = float(np.mean(harmonic ** 2))
                noise_energy = float(np.mean(percussive ** 2))
                features.hnr_mean = float(10 * np.log10((harmonic_energy + 1e-9) / (noise_energy + 1e-9)))

            mfcc = librosa.feature.mfcc(y=y_norm, sr=sr, n_mfcc=13, hop_length=hop_length)
            features.mfcc_mean = [float(v) for v in np.mean(mfcc, axis=1)]
            features.mfcc_std = [float(v) for v in np.std(mfcc, axis=1)]

            features.snr_estimate = self._estimate_snr(rms)
            features.breathiness_index = self._clamp(
                self._risk_high(features.spectral_flatness_mean, 0.08, 0.35) * 0.45 +
                self._risk_low(features.hnr_mean, 18, 4) * 0.35 +
                self._risk_high(features.pause_ratio, 0.25, 0.55) * 0.20
            )
            features.hoarseness_index = self._clamp(
                self._risk_high(features.jitter_local, 0.015, 0.08) * 0.35 +
                self._risk_high(features.shimmer_local, 0.08, 0.35) * 0.35 +
                self._risk_low(features.hnr_mean, 20, 6) * 0.30
            )
            features.articulation_stability = self._clamp(
                100 -
                self._risk_low(features.spectral_flux_std, 0.10, 0.02) * 0.35 -
                self._risk_high(features.pause_ratio, 0.25, 0.55) * 0.25 -
                self._risk_outside(features.speech_rate, 2.0, 7.5, 3.0) * 0.40
            )
            features.signal_quality = self._clamp(
                self._risk_low(features.snr_estimate, 24, 6) * -0.45 +
                self._risk_high(features.clipping_ratio, 0.001, 0.04) * -0.25 +
                self._risk_low(features.total_duration, 20, 3) * -0.20 +
                100
            )

        except Exception as exc:
            print(f"特征提取失败: {exc}")
            return self._fallback(features)

        return features

    @staticmethod
    def _pause_stats(is_voice: np.ndarray, hop_length: int, sr: int):
        if is_voice.size < 2:
            return 0, 0.0

        pauses = []
        start = None
        for idx, active in enumerate(is_voice):
            if not active and start is None:
                start = idx
            elif active and start is not None:
                pauses.append((idx - start) * hop_length / sr)
                start = None
        if start is not None:
            pauses.append((len(is_voice) - start) * hop_length / sr)

        meaningful = [p for p in pauses if p >= 0.12]
        if not meaningful:
            return 0, 0.0
        return len(meaningful), float(np.mean(meaningful))

    @staticmethod
    def _estimate_snr(rms: np.ndarray) -> float:
        if rms.size < 4:
            return 0.0
        speech = np.percentile(rms, 90)
        noise = max(np.percentile(rms, 10), 1e-6)
        return float(20 * np.log10((speech + 1e-6) / noise))

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

    @classmethod
    def _risk_outside(cls, value: float, low: float, high: float, span: float) -> float:
        if low <= value <= high:
            return 0.0
        if value < low:
            return cls._risk_low(value, low, low - span)
        return cls._risk_high(value, high, high + span)

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return float(max(low, min(high, value)))

    def _fallback(self, features: AcousticFeatures) -> AcousticFeatures:
        features.total_duration = 30.0
        features.f0_mean = 150.0
        features.f0_std = 18.0
        features.f0_min = 110.0
        features.f0_max = 210.0
        features.f0_range = 100.0
        features.voiced_ratio = 0.65
        features.speech_rate = 4.0
        features.hnr_mean = 18.0
        features.signal_quality = 50.0
        features.articulation_stability = 70.0
        features.volume_stability = 70.0
        return features


def extract_features(audio_path: str, sr: int = 16000) -> AcousticFeatures:
    ext = FeatureExtractor(sr=sr)
    return ext.extract(audio_path)
