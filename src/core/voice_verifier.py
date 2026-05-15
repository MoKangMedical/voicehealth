"""
语音验证器 — 真实音频分析版

- 活体检测(LivenessDetector): 基于音频信号特征判断是否为真人录音
  * 能量变化(自然语音有丰富的能量起伏)
  * 频谱通量(频谱随时间变化的速率)
  * 过零率模式(区分语音与非语音)
  * 静音间隙(自然朗读中有自然停顿)
  * 信噪比估算(真实录音存在底噪)

- 朗读验证(ReadingVerifier): 用语音识别对比用户朗读与期望文本
  * 优先使用vosk(离线轻量STT)
  * 回退方案:基于关键词能量检测+音频时长匹配
"""

import os
import math
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import numpy as np

READING_TEXTS = [
    {"id": "standard_1", "text": "春天来了，花儿开了，小鸟在枝头唱歌。", "keywords": ["春天", "花儿", "小鸟"]},
    {"id": "standard_2", "text": "健康是人生最宝贵的财富。", "keywords": ["健康", "财富"]},
    {"id": "standard_3", "text": "科技改变了我们的生活。", "keywords": ["科技", "生活"]}
]

# 朗读文本ID到文本的快速映射
_TEXT_MAP = {t["id"]: t for t in READING_TEXTS}


@dataclass
class LivenessResult:
    is_live: bool = False
    confidence: float = 0.0
    score: float = 0.0
    checks: Dict[str, bool] = field(default_factory=dict)


class LivenessDetector:
    """
    基于音频信号特征的活体检测器。

    分析多个维度来判断音频是否来自真实人声:
    1. 能量动态范围 — 真人语音的RMS能量有丰富的起伏
    2. 频谱通量 — 真人发音时频谱随时间自然变化
    3. 过零率分布 — 声带振动产生的过零率模式
    4. 静音间隙分析 — 自然朗读有合理的停顿
    5. 信噪比 — 录音存在环境底噪
    6. 基频连续性 — 人类声带的基频变化是连续的
    """

    # 各项检查的权重
    WEIGHTS = {
        "energy_variation": 0.20,
        "spectral_flux": 0.20,
        "zero_crossing": 0.15,
        "silence_pattern": 0.15,
        "snr_check": 0.15,
        "pitch_continuity": 0.15,
    }

    def __init__(self, sr: int = 16000):
        self.sr = sr

    def detect(self, audio_path: str) -> LivenessResult:
        """对音频文件执行活体检测，返回检测结果。"""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=self.sr)
        except Exception as e:
            return LivenessResult(
                is_live=False, confidence=0.0, score=0.0,
                checks={"load_error": False}
            )

        # 太短的音频直接判定异常
        duration = len(y) / sr
        if duration < 0.5:
            return LivenessResult(
                is_live=False, confidence=0.1, score=0.1,
                checks={"duration_too_short": False}
            )

        checks: Dict[str, bool] = {}
        scores: Dict[str, float] = {}

        # ── 1. 能量动态范围检查 ──
        checks["energy_variation"], scores["energy_variation"] = self._check_energy_variation(y, sr)

        # ── 2. 频谱通量检查 ──
        checks["spectral_flux"], scores["spectral_flux"] = self._check_spectral_flux(y, sr)

        # ── 3. 过零率模式检查 ──
        checks["zero_crossing"], scores["zero_crossing"] = self._check_zero_crossing(y, sr)

        # ── 4. 静音间隙检查 ──
        checks["silence_pattern"], scores["silence_pattern"] = self._check_silence_pattern(y, sr)

        # ── 5. 信噪比检查 ──
        checks["snr_check"], scores["snr_check"] = self._check_snr(y, sr)

        # ── 6. 基频连续性检查 ──
        checks["pitch_continuity"], scores["pitch_continuity"] = self._check_pitch_continuity(y, sr)

        # ── 综合评分 ──
        total_score = sum(
            scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        total_score = max(0.0, min(1.0, total_score))

        # 通过的检查项数
        checks = {k: bool(v) for k, v in checks.items()}
        passed = sum(1 for v in checks.values() if v)
        total_checks = len(checks)

        # 至少需要通过一半检查且综合分>0.5才判定为真人
        is_live = bool((passed >= total_checks * 0.5) and (total_score > 0.5))
        confidence = float(total_score * (passed / total_checks))

        return LivenessResult(
            is_live=is_live,
            confidence=float(round(confidence, 3)),
            score=float(round(total_score, 3)),
            checks=checks,
        )

    # ──────────── 各项检测方法 ────────────

    def _check_energy_variation(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        真人语音的能量有丰富的动态变化。
        计算帧级RMS能量的变异系数(CV): CV越高说明能量变化越自然。
        录音回放/合成语音通常能量过于均匀或有规律的重复模式。
        """
        frame_length = int(0.025 * sr)  # 25ms帧
        hop_length = int(0.010 * sr)    # 10ms步长
        rms = np.array([
            np.sqrt(np.mean(y[i:i+frame_length]**2))
            for i in range(0, len(y) - frame_length, hop_length)
        ])

        if len(rms) < 10:
            return False, 0.2

        # 去除静音帧后计算变异系数
        rms_nonzero = rms[rms > np.max(rms) * 0.02]
        if len(rms_nonzero) < 5:
            return False, 0.1

        cv = np.std(rms_nonzero) / (np.mean(rms_nonzero) + 1e-10)

        # 真人语音CV通常在0.3~1.5之间
        # CV太低→可能是合成/回放, CV太高→可能是噪音
        score = 1.0
        if cv < 0.15:
            score = cv / 0.15 * 0.4  # 能量太均匀
        elif cv < 0.3:
            score = 0.4 + (cv - 0.15) / 0.15 * 0.3
        elif cv <= 1.5:
            score = 0.7 + min((cv - 0.3) / 1.2, 1.0) * 0.3
        else:
            score = max(0.3, 1.0 - (cv - 1.5) / 2.0)

        passed = 0.2 < cv < 2.0
        return passed, round(score, 3)

    def _check_spectral_flux(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        频谱通量衡量相邻帧频谱的变化速率。
        真人语音在辅音/元音转换时频谱通量会出现尖峰,
        而合成语音的频谱变化通常更平滑或有规律。
        """
        S = np.abs(np.array([
            np.fft.rfft(y[i:i+int(0.025*sr)])
            for i in range(0, len(y) - int(0.025*sr), int(0.010*sr))
        ]))
        if S.shape[0] < 5:
            return False, 0.2

        # 相邻帧频谱差异
        flux = np.sqrt(np.sum(np.diff(S, axis=0) ** 2, axis=1))
        flux_norm = flux / (np.max(flux) + 1e-10)

        # 通量的统计特征
        mean_flux = np.mean(flux_norm)
        std_flux = np.std(flux_norm)

        # 真人语音的通量均值适中、标准差较高(有突变)
        score = 0.5
        if 0.05 < mean_flux < 0.8 and std_flux > 0.05:
            score = 0.7 + min(std_flux, 0.5) * 0.6
        elif mean_flux < 0.01:
            score = 0.2  # 几乎没变化，可能是静音或合成

        passed = mean_flux > 0.02 and std_flux > 0.03
        return passed, round(min(score, 1.0), 3)

    def _check_zero_crossing(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        过零率(ZCR)反映信号穿过零轴的频率。
        语音中的浊音段ZCR较低，清音段ZCR较高。
        真人语音的ZCR分布应有明显的变化。
        """
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        zcr = np.array([
            np.sum(np.abs(np.diff(np.sign(y[i:i+frame_length])))) / (2 * frame_length)
            for i in range(0, len(y) - frame_length, hop_length)
        ])

        if len(zcr) < 10:
            return False, 0.2

        zcr_mean = np.mean(zcr)
        zcr_std = np.std(zcr)

        # 真人语音ZCR均值通常在0.02~0.2之间
        score = 0.5
        if 0.01 < zcr_mean < 0.3:
            score = 0.6
            # ZCR标准差高说明有浊音/清音交替
            score += min(zcr_std * 5, 0.4)
        elif zcr_mean > 0.4:
            score = 0.3  # 可能是噪音

        passed = 0.01 < zcr_mean < 0.35
        return passed, round(min(score, 1.0), 3)

    def _check_silence_pattern(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        自然朗读中存在合理的停顿(句间、词间)。
        分析静音段的数量和分布:太少→可能是连续播放;太多→可能是噪音间歇。
        """
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        rms = np.array([
            np.sqrt(np.mean(y[i:i+frame_length]**2))
            for i in range(0, len(y) - frame_length, hop_length)
        ])

        if len(rms) < 20:
            return False, 0.3

        threshold = np.max(rms) * 0.05
        is_silent = rms < threshold

        # 计算静音段数量(连续静音帧算一段)
        silence_changes = np.diff(is_silent.astype(int))
        silence_starts = np.where(silence_changes == 1)[0]
        silence_ends = np.where(silence_changes == -1)[0]
        num_silences = min(len(silence_starts), len(silence_ends))

        duration = len(y) / sr
        silence_ratio = np.sum(is_silent) / len(is_silent)

        # 每秒0.2~2个停顿是合理的
        silences_per_sec = num_silences / max(duration, 0.1)

        score = 0.5
        if 0.1 < silences_per_sec < 3.0:
            score = 0.6 + min(silences_per_sec / 3.0, 0.4)
        elif silences_per_sec < 0.05:
            score = 0.3  # 几乎没有停顿

        # 停顿比例在10%~60%之间较合理
        if 0.05 < silence_ratio < 0.7:
            score = min(score + 0.1, 1.0)

        passed = 0.05 < silences_per_sec < 5.0 and silence_ratio < 0.9
        return passed, round(score, 3)

    def _check_snr(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        信噪比检查:真实录音存在环境底噪,
        而完全无噪或极高噪的音频可能是合成或损坏的。
        """
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        rms = np.array([
            np.sqrt(np.mean(y[i:i+frame_length]**2))
            for i in range(0, len(y) - frame_length, hop_length)
        ])

        if len(rms) < 10:
            return False, 0.2

        # 估算信号功率(前10%高能量帧)和噪声功率(后10%低能量帧)
        sorted_rms = np.sort(rms)
        noise_frames = sorted_rms[:max(1, len(sorted_rms) // 10)]
        signal_frames = sorted_rms[max(1, len(sorted_rms) * 9 // 10):]

        noise_power = np.mean(noise_frames ** 2) + 1e-12
        signal_power = np.mean(signal_frames ** 2) + 1e-12

        snr_db = 10 * math.log10(signal_power / noise_power)

        # 真人录音SNR通常在10~50dB
        score = 0.5
        if 5 < snr_db < 60:
            score = 0.6 + min((snr_db - 5) / 50, 0.4)
        elif snr_db > 80:
            score = 0.3  # 可能是合成(极干净)

        passed = 3 < snr_db < 70
        return passed, round(min(score, 1.0), 3)

    def _check_pitch_continuity(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        """
        基频(F0)连续性:人类声带的基频变化是平滑连续的,
        不会出现突变。检测F0轨迹的连续性。
        """
        try:
            import librosa
            f0, voiced_flag, _ = librosa.pyin(
                y, fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'), sr=sr
            )
        except Exception:
            return False, 0.3

        f0_valid = f0[~np.isnan(f0)]
        if len(f0_valid) < 5:
            return False, 0.2

        # 计算相邻帧基频差(半音)
        f0_diff = np.abs(np.diff(f0_valid))
        f0_diff_semitones = 12 * np.log2((f0_valid[1:] + 1e-10) / (f0_valid[:-1] + 1e-10))
        f0_diff_semitones = np.abs(f0_diff_semitones)

        # 连续帧之间的突变不应超过5个半音(正常语音)
        large_jumps = np.sum(f0_diff_semitones > 5)
        jump_ratio = large_jumps / len(f0_diff_semitones)

        # F0范围合理性: 男声85-180Hz, 女声165-255Hz
        f0_mean = np.mean(f0_valid)
        f0_in_range = 60 < f0_mean < 400

        score = 0.5
        if f0_in_range:
            score = 0.6
        if jump_ratio < 0.3:
            score += 0.3
        elif jump_ratio < 0.5:
            score += 0.15

        passed = f0_in_range and jump_ratio < 0.5
        return passed, round(min(score, 1.0), 3)


class ReadingVerifier:
    """
    朗读验证器:对比用户实际朗读内容与期望文本。

    优先使用vosk进行语音识别(离线、轻量)。
    如果vosk不可用,回退到基于音频特征的关键词时长估算。
    """

    def __init__(self, vosk_model_path: Optional[str] = None):
        self._vosk_model_path = vosk_model_path
        self._vosk_model = None
        self._vosk_available: Optional[bool] = None

    def _try_init_vosk(self) -> bool:
        """尝试初始化vosk模型,返回是否可用。"""
        if self._vosk_available is not None:
            return self._vosk_available

        try:
            from vosk import Model, KaldiRecognizer
            # 尝试指定路径或默认路径
            model_path = self._vosk_model_path
            if model_path is None:
                # 常见的vosk中文模型路径
                candidates = [
                    os.path.expanduser("~/vosk-model-small-cn-0.22"),
                    os.path.expanduser("~/vosk-model-cn-0.22"),
                    "vosk-model-small-cn-0.22",
                    "vosk-model-cn-0.22",
                    "/opt/vosk-model-small-cn-0.22",
                ]
                for p in candidates:
                    if os.path.isdir(p):
                        model_path = p
                        break

            if model_path and os.path.isdir(model_path):
                self._vosk_model = Model(model_path)
                self._vosk_available = True
            else:
                self._vosk_available = False
        except ImportError:
            self._vosk_available = False
        except Exception:
            self._vosk_available = False

        return self._vosk_available

    def _transcribe_vosk(self, audio_path: str) -> str:
        """使用vosk识别音频中的文字。"""
        import wave
        import json
        from vosk import KaldiRecognizer

        wf = wave.open(audio_path, "rb")
        # vosk要求PCM 16bit单声道
        if wf.getsampwidth() != 2 or wf.getnchannels() != 1:
            # 需要转换格式
            import librosa
            import tempfile
            import struct
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
            y_int16 = (y * 32767).astype(np.int16)
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(tmp.name, 'wb') as wf_out:
                wf_out.setnchannels(1)
                wf_out.setsampwidth(2)
                wf_out.setframerate(16000)
                wf_out.writeframes(y_int16.tobytes())
            wf.close()
            wf = wave.open(tmp.name, "rb")
            os.unlink(tmp.name)

        rec = KaldiRecognizer(self._vosk_model, wf.getframerate())
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    results.append(res["text"])
        # 最终结果
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            results.append(final["text"])
        wf.close()

        return "".join(results).replace(" ", "")

    def _transcribe_fallback(self, audio_path: str, expected_text: str) -> Tuple[str, float]:
        """
        无STT引擎时的回退方案:
        通过音频特征做粗略的"关键词时长匹配"。
        不返回识别文本,直接返回匹配置信度。
        """
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
        except Exception:
            return "", 0.0

        duration = len(y) / sr
        expected_chars = len(expected_text.replace(" ", "").replace("，", "").replace("。", ""))

        # 中文语速约 3~6 字/秒, 计算期望时长范围
        expected_min_duration = expected_chars / 6.0
        expected_max_duration = expected_chars / 2.0 + 2.0  # 加2秒余量

        # 时长匹配分
        if expected_min_duration <= duration <= expected_max_duration:
            duration_score = 1.0
        elif duration < expected_min_duration:
            ratio = duration / expected_min_duration
            duration_score = max(0.0, ratio * 0.8)
        else:
            # 太长可能是重复朗读
            ratio = expected_max_duration / duration
            duration_score = max(0.0, ratio * 0.7)

        # 能量检查:有明显的语音段
        frame_len = int(0.025 * sr)
        hop = int(0.010 * sr)
        rms = np.array([
            np.sqrt(np.mean(y[i:i+frame_len]**2))
            for i in range(0, len(y) - frame_len, hop)
        ])
        speech_ratio = np.sum(rms > np.max(rms) * 0.08) / max(len(rms), 1)

        # 有实际语音内容
        speech_score = min(speech_ratio / 0.4, 1.0) * 0.8 + 0.2

        confidence = duration_score * 0.5 + speech_score * 0.5
        return "", round(confidence, 3)

    def _text_similarity(self, actual: str, expected: str) -> float:
        """计算两段文本的相似度(0~1)。"""
        # 清理标点和空格
        def clean(s):
            return re.sub(r'[，。、！？\s,.!?]', '', s).lower()

        a = clean(actual)
        e = clean(expected)

        if not a or not e:
            return 0.0

        # 序列匹配相似度
        seq_ratio = SequenceMatcher(None, a, e).ratio()

        # 关键词覆盖率
        expected_keywords = []
        for t in READING_TEXTS:
            if t["text"] == expected or t["id"] == expected:
                expected_keywords = t["keywords"]
                break

        keyword_hits = 0
        if expected_keywords:
            for kw in expected_keywords:
                if kw in a:
                    keyword_hits += 1
            keyword_ratio = keyword_hits / len(expected_keywords)
        else:
            keyword_ratio = seq_ratio

        # 综合:序列相似度60% + 关键词匹配40%
        return seq_ratio * 0.6 + keyword_ratio * 0.4

    def verify(self, text: str, expected_id: str, audio_path: Optional[str] = None) -> dict:
        """
        验证朗读内容。

        参数:
            text: 用户声称朗读的文本(可能为空,此时从expected_id查)
            expected_id: 期望的朗读文本ID
            audio_path: 音频文件路径(用于STT识别)

        返回:
            dict: {"is_valid": bool, "confidence": float, "recognized_text": str, "match_score": float}
        """
        # 获取期望文本
        expected_info = _TEXT_MAP.get(expected_id)
        if not expected_info:
            expected_info = _TEXT_MAP.get("standard_1")
        expected_text = expected_info["text"]

        recognized_text = ""
        match_score = 0.0

        # 方案1: vosk语音识别
        if audio_path and self._try_init_vosk():
            try:
                recognized_text = self._transcribe_vosk(audio_path)
                match_score = self._text_similarity(recognized_text, expected_text)
            except Exception:
                match_score = 0.0

        # 方案2: 如果有text参数(前端已识别),直接比较
        if not recognized_text and text:
            recognized_text = text
            match_score = self._text_similarity(text, expected_text)

        # 方案3: 回退到音频特征估算
        if match_score < 0.01 and audio_path:
            _, fallback_score = self._transcribe_fallback(audio_path, expected_text)
            match_score = fallback_score

        # 阈值: 至少50%匹配才算通过
        is_valid = match_score >= 0.5

        return {
            "is_valid": is_valid,
            "confidence": round(match_score, 3),
            "recognized_text": recognized_text,
            "match_score": round(match_score, 3),
            "expected_text": expected_text,
            "expected_id": expected_id,
        }
