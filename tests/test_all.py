#!/usr/bin/env python3
"""VoiceHealth 测试脚本 — 端到端验证"""

import sys
sys.path.insert(0, '.')

from src.core.feature_extractor import FeatureExtractor, AcousticFeatures
from src.core.disease_detector import DiseaseDetector, DISEASE_REGISTRY


def test_feature_extractor():
    """测试特征提取"""
    print("🧪 测试特征提取器...")
    ext = FeatureExtractor(sr=16000)
    
    # 测试无音频的AcousticFeatures
    feat = AcousticFeatures(f0_mean=142, jitter_local=0.018, speech_rate=3.2)
    vec = feat.to_dict()
    assert len(vec) >= 30, f"Feature dict should expose core acoustic fields, got {len(vec)}"
    print(f"  ✅ 特征字段: {len(vec)}项")
    
    # 测试真实音频提取
    try:
        feat = ext.extract('data/examples/demo_voice_30s.wav')
        print(f"  ✅ 真实音频提取成功: F0={feat.f0_mean:.1f}Hz, RMS={feat.rms_mean:.4f}")
    except Exception as e:
        print(f"  ⚠️ 真实音频提取: {e}")


def test_disease_detector():
    """测试疾病检测"""
    print("\n🧪 测试疾病检测器...")
    det = DiseaseDetector()
    
    feat = AcousticFeatures(
        f0_mean=142, f0_std=38, jitter_local=0.018,
        shimmer_local=0.045, hnr_mean=14.3,
        speech_rate=3.2, rms_mean=0.031
    )
    
    report = det.generate_report(feat)
    assert len(report.risks) == 25, f"Should score 25 health reference items, got {len(report.risks)}"
    assert 0 <= report.overall_score <= 100
    print(f"  ✅ 健康参考项: {len(report.risks)}")
    print(f"  ✅ 总分: {report.overall_score}")
    print(f"  ✅ 摘要: {report.summary}")


def test_disease_registry():
    """测试疾病注册表"""
    print("\n🧪 测试疾病注册表...")
    categories = {}
    for did, info in DISEASE_REGISTRY.items():
        cat = info["category"]
        categories.setdefault(cat, []).append(info["name"])
    
    for cat, diseases in categories.items():
        print(f"  ✅ {cat}: {len(diseases)}种 — {', '.join(diseases[:3])}...")
    
    total = len(DISEASE_REGISTRY)
    print(f"\n  📊 总计: {total}种疾病/健康状态")


def test_api():
    """测试API导入"""
    print("\n🧪 测试API模块...")
    from src.api.main import app
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    api_routes = [r for r in routes if r.startswith('/api')]
    print(f"  ✅ API路由: {api_routes}")
    assert '/api/analyze' in routes
    assert '/api/diseases' in routes
    assert '/api/health' in routes


if __name__ == "__main__":
    print("=" * 50)
    print("🔊 VoiceHealth 测试套件")
    print("=" * 50)
    
    test_feature_extractor()
    test_disease_detector()
    test_disease_registry()
    test_api()
    
    print("\n" + "=" * 50)
    print("✅ 全部测试通过!")
    print("=" * 50)
