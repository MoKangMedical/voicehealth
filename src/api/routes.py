"""
VoiceHealth — 完整API路由

闭环系统API：
- 用户系统 (注册/登录/信息)
- 语音分析 (录音/验证/分析)
- 面部分析 (拍照/分析)
- 视频分析 (录制/分析)
- 报告管理 (查询/历史)
- 订单支付 (创建/回调)
- 统计趋势 (数据/图表)
"""

import os
import sys
import tempfile
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends, Query
from pydantic import BaseModel, Field

from src.core.database import db
from src.core.feature_extractor import FeatureExtractor
from src.core.disease_detector import DiseaseDetector, DISEASE_REGISTRY
from src.core.voice_verifier import LivenessDetector, ReadingVerifier, READING_TEXTS
from src.core.face_analyzer import FaceAnalyzer
from src.core.video_analyzer import VideoAnalyzer
from src.core.evidence_base import get_evidence_base
from src.core.health_plan import build_action_plan
from src.core.evidence_health_plans import (
    get_evidence_health_plan,
    get_evidence_health_plans,
    match_evidence_health_plans,
)

router = APIRouter(prefix="/api/v1", tags=["VoiceHealth API"])

extractor = FeatureExtractor(sr=16000)
detector = DiseaseDetector()
liveness_detector = LivenessDetector(sr=16000)
reading_verifier = ReadingVerifier()
face_analyzer = FaceAnalyzer()
video_analyzer = VideoAnalyzer()

HEALTH_DATA_SCHEMA_VERSION = "vh.health.v1"
PUBLIC_REPORT_TYPES = ("all", "voice", "face", "video", "combined")
INTEGRATION_SCOPES = [
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
    "health.evidence_plan.read",
]


# ═══════ 数据模型 ═══════

class UserRegister(BaseModel):
    openid: str
    nickname: str = ""
    avatar_url: str = ""

class WechatLogin(BaseModel):
    code: Optional[str] = None
    client_id: Optional[str] = None
    openid: Optional[str] = None
    nickname: str = ""
    avatar_url: str = ""

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None

class OrderCreate(BaseModel):
    type: str  # single, vip_monthly
    amount: int

class OrderCallback(BaseModel):
    order_no: str
    status: str
    payment_id: str = ""

class CombinedAnalyze(BaseModel):
    voice_report_id: Optional[str] = None
    face_report_id: Optional[str] = None
    video_report_id: Optional[str] = None

class LifestyleCheckin(BaseModel):
    checkinDate: Optional[str] = None
    breakfast: str = ""
    lunch: str = ""
    dinner: str = ""
    snack: str = ""
    dietTags: List[str] = Field(default_factory=list)
    waterMl: int = 0
    caffeineCups: float = 0
    alcohol: bool = False
    spicyOily: bool = False
    lateMeal: bool = False
    exerciseType: str = ""
    exerciseMinutes: int = 0
    exerciseIntensity: str = ""
    steps: int = 0
    sleepHours: float = 0
    stressLevel: int = 0
    mood: str = ""
    symptoms: List[str] = Field(default_factory=list)
    notes: str = ""
    source: str = "mini_program"

class ImprovementCycleCreate(BaseModel):
    reportId: Optional[str] = None
    days: int = 14

class ImprovementProgressUpdate(BaseModel):
    checkinDate: Optional[str] = None
    completedActionIds: List[str] = Field(default_factory=list)
    skippedActionIds: List[str] = Field(default_factory=list)
    moodScore: int = 0
    energyScore: int = 0
    note: str = ""

class ImprovementCycleStatusUpdate(BaseModel):
    status: str


# ═══════ 用户系统 ═══════

@router.post("/user/register")
async def register_user(data: UserRegister):
    """用户注册/登录"""
    user = db.get_or_create_user(data.openid, data.nickname, data.avatar_url)
    stats = db.get_user_stats(user['id'])
    return {
        "ok": True,
        "user": user,
        "stats": stats,
        "is_vip": db.check_vip_status(user['id'])
    }

@router.post("/user/wechat-login")
async def wechat_login(data: WechatLogin):
    """
    微信小程序登录。

    生产环境配置 WECHAT_APP_ID / WECHAT_APP_SECRET 后，会用 wx.login 的 code
    换取 openid；本地开发可传 client_id 作为稳定开发身份。
    """
    openid = data.openid

    app_id = os.getenv("WECHAT_APP_ID")
    app_secret = os.getenv("WECHAT_APP_SECRET")
    if data.code and app_id and app_secret:
        openid = _exchange_wechat_code(data.code, app_id, app_secret)

    if not openid:
        if not data.client_id:
            raise HTTPException(400, "缺少微信code或本地开发client_id")
        openid = f"dev_{data.client_id}"

    user = db.get_or_create_user(openid, data.nickname, data.avatar_url)
    if data.nickname or data.avatar_url:
        db.update_user(user['id'], nickname=data.nickname, avatar_url=data.avatar_url)
        user = db.get_user(user['id'])

    stats = db.get_user_stats(user['id'])
    return {
        "ok": True,
        "user": user,
        "stats": stats,
        "is_vip": db.check_vip_status(user['id'])
    }

@router.get("/user/profile")
async def get_profile(user_id: str = Header(..., alias="X-User-Id")):
    """获取用户信息"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    
    stats = db.get_user_stats(user_id)
    return {
        "ok": True,
        "user": user,
        "stats": stats,
        "is_vip": db.check_vip_status(user_id)
    }

@router.get("/user/stats")
async def get_user_stats_alias(user_id: str = Header(..., alias="X-User-Id")):
    """小程序个人中心统计别名。"""
    return {"ok": True, "stats": db.get_user_stats(user_id)}

@router.put("/user/profile")
async def update_profile(
    data: UserUpdate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """更新用户信息"""
    db.update_user(user_id, **data.dict(exclude_none=True))
    user = db.get_user(user_id)
    return {"ok": True, "user": user}


def _exchange_wechat_code(code: str, app_id: str, app_secret: str) -> str:
    params = urllib.parse.urlencode({
        "appid": app_id,
        "secret": app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    })
    url = f"https://api.weixin.qq.com/sns/jscode2session?{params}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(502, f"微信登录服务不可用: {exc}") from exc

    if payload.get("errcode"):
        raise HTTPException(401, payload.get("errmsg", "微信登录失败"))
    if not payload.get("openid"):
        raise HTTPException(401, "微信登录未返回openid")
    return payload["openid"]


# ═══════ 语音分析 ═══════

@router.post("/voice/analyze")
async def analyze_voice(
    audio: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-Id"),
    reading_text_id: str = Query(default="standard_1")
):
    """
    完整语音分析流程：
    1. 验证用户权限
    2. 活体检测
    3. 朗读验证
    4. 声学特征提取
    5. 声音健康风险参考
    6. 生成报告
    """
    # 检查用户权限
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")
    
    is_vip = db.check_vip_status(user_id)
    if not is_vip:
        if not db.use_free_count(user_id):
            raise HTTPException(403, "免费次数已用完，请开通VIP")
    
    # 保存音频文件
    suffix = Path(audio.filename or "audio.wav").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 1. 活体检测（基于音频信号特征的真实分析）
        liveness_result = liveness_detector.detect(tmp_path)

        # 2. 朗读验证（vosk STT + 模糊匹配, 或音频特征回退）
        reading_result = reading_verifier.verify(
            text="",
            expected_id=reading_text_id,
            audio_path=tmp_path,
        )
        reading_match = reading_result["match_score"]
        
        # 3. 提取声学特征
        features = extractor.extract(tmp_path)
        
        # 4. 生成声音健康风险参考报告
        report = detector.generate_report(features)
        report_dict = report.to_dict()
        
        # 5. 保存报告
        feature_vector = features.to_dict()
        voice_report = {
            'overall_score': report_dict.get('overall_score', 75),
            'summary': report_dict.get('summary', '声纹特征分析完成'),
            'features': report_dict.get('features', []),
            'risks': report_dict.get('risks', []),
            'domains': report_dict.get('domains', []),
            'voice_quality': report_dict.get('voice_quality', {}),
            'feature_vector': feature_vector,
            'ai_insight': report_dict.get('ai_insight', '基于声纹分析，建议保持良好作息习惯。'),
            'reading_text_id': reading_text_id,
            'reading_match_score': reading_match,
            'recognized_text': reading_result.get('recognized_text', ''),
            'liveness_score': liveness_result.score,
            'liveness_checks': liveness_result.checks,
            'duration': features.total_duration
        }
        
        report_id = db.save_voice_report(user_id, voice_report)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        return {
            "ok": True,
            "report_id": report_id,
            "report": voice_report,
            "liveness": {
                "is_live": liveness_result.is_live,
                "score": liveness_result.score
            }
        }
        
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(500, f"分析失败: {str(e)}")


@router.get("/voice/report/{report_id}")
async def get_voice_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取语音报告"""
    report = db.get_voice_report(report_id)
    if not report:
        raise HTTPException(404, "报告不存在")
    if report['user_id'] != user_id:
        raise HTTPException(403, "无权访问")
    return {"ok": True, "report": report}


@router.get("/voice/history")
async def get_voice_history(
    user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0)
):
    """获取语音检测历史"""
    reports = db.get_user_voice_reports(user_id, limit, offset)
    return {"ok": True, "records": reports, "total": len(reports)}


# ═══════ 面部分析 ═══════

@router.post("/face/analyze")
async def analyze_face(
    image: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-Id")
):
    """面部分析"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")

    # 保存图片到临时文件
    suffix = Path(image.filename or "image.jpg").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 调用真实面部分析模块
        result = face_analyzer.analyze(tmp_path)
        face_report = result.to_dict()

        report_id = db.save_face_report(user_id, face_report)

        os.unlink(tmp_path)

        return {
            "ok": True,
            "report_id": report_id,
            "report": face_report
        }

    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(500, f"面部分析失败: {str(e)}")


@router.get("/face/report/{report_id}")
async def get_face_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取面部报告"""
    report = db.get_face_report(report_id)
    if not report:
        raise HTTPException(404, "报告不存在")
    if report['user_id'] != user_id:
        raise HTTPException(403, "无权访问")
    return {"ok": True, "report": report}


# ═══════ 视频分析 ═══════

@router.post("/video/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-Id"),
    detect_items: str = Query(default="skin,eye,hair")
):
    """视频分析"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")

    items = [i.strip() for i in detect_items.split(',')]

    # 保存视频到临时文件
    suffix = Path(video.filename or "video.mp4").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await video.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 调用真实视频分析模块
        analysis = video_analyzer.analyze_video(tmp_path)
        analysis_dict = analysis.to_dict()

        # 构建符合前端期望格式的结果
        result = {
            'overall_score': int(analysis_dict.get('overall_health_score', 0)),
            'biological_age': 0,
            'detect_items': items,
            'frame_count': analysis_dict.get('frame_count', 0),
            'video_duration': analysis_dict.get('video_duration', 0),
            'summary': analysis_dict.get('summary', ''),
        }

        if 'skin' in items and analysis_dict.get('skin'):
            skin = analysis_dict['skin']
            result['skin'] = {
                'overall_score': int(skin.get('health_score', 0)),
                'skin_tone': skin.get('skin_tone', ''),
                'skin_brightness': skin.get('skin_brightness', 0),
                'skin_uniformity': skin.get('skin_uniformity', 0),
                'texture_score': skin.get('texture_score', 0),
                'oiliness_score': skin.get('oiliness_score', 0),
                'summary': skin.get('summary', ''),
                'suggestions': []
            }

        if 'eye' in items and analysis_dict.get('eye'):
            eye = analysis_dict['eye']
            result['eye'] = {
                'overall_score': int(eye.get('health_score', 0)),
                'fatigue_score': eye.get('fatigue_score', 0),
                'blink_rate': eye.get('blink_rate', 0),
                'summary': eye.get('summary', ''),
                'suggestions': []
            }

        if 'hair' in items and analysis_dict.get('hair'):
            hair = analysis_dict['hair']
            result['hair'] = {
                'overall_score': int(hair.get('health_score', 0)),
                'hair_color': hair.get('hair_color', ''),
                'hair_shine': hair.get('hair_shine', 0),
                'summary': hair.get('summary', ''),
                'suggestions': []
            }

        report_id = db.save_video_report(user_id, result)

        os.unlink(tmp_path)

        return {
            "ok": True,
            "report_id": report_id,
            "result": result
        }

    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(500, f"视频分析失败: {str(e)}")


@router.get("/video/report/{report_id}")
async def get_video_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取视频报告"""
    report = db.get_video_report(report_id)
    if not report:
        raise HTTPException(404, "报告不存在")
    if report['user_id'] != user_id:
        raise HTTPException(403, "无权访问")
    return {"ok": True, "report": report}


# ═══════ 综合评估 ═══════

@router.post("/combined/analyze")
async def analyze_combined(
    data: CombinedAnalyze,
    user_id: str = Header(..., alias="X-User-Id")
):
    """基于用户最近的语音/面部/视频报告生成综合健康评估。"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")

    source_reports = _resolve_combined_sources(user_id, data)
    if not source_reports:
        raise HTTPException(400, "请先完成至少一次语音、面部或视频检测")

    combined_report = _build_combined_report(source_reports)
    report_id = db.save_combined_report(user_id, combined_report)

    saved = db.get_combined_report(report_id) or combined_report
    saved["type"] = "combined"
    return {
        "ok": True,
        "report_id": report_id,
        "report": _normalize_report_for_api(saved),
        "sources": [_normalize_report_for_api(report) for report in source_reports]
    }


@router.get("/combined/report/{report_id}")
async def get_combined_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取综合评估报告。"""
    report = db.get_combined_report(report_id)
    if not report:
        raise HTTPException(404, "报告不存在")
    if report['user_id'] != user_id:
        raise HTTPException(403, "无权访问")
    report["type"] = "combined"
    return {"ok": True, "report": _normalize_report_for_api(report)}


# ═══════ 统一报告接口（小程序直接使用） ═══════

@router.get("/report/list")
async def list_reports(
    user_id: str = Header(..., alias="X-User-Id"),
    report_type: str = Query(default="all", alias="type"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    offset: Optional[int] = Query(default=None, ge=0)
):
    """获取语音/面部/视频统一历史记录。"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")

    if report_type not in ("all", "voice", "face", "video", "combined"):
        raise HTTPException(400, "报告类型不支持")

    real_offset = offset if offset is not None else (page - 1) * limit
    reports = db.get_user_reports(user_id, report_type, limit, real_offset)
    normalized = [_normalize_report_for_api(report) for report in reports]
    return {
        "ok": True,
        "reports": normalized,
        "records": normalized,
        "total": len(normalized),
        "page": page,
        "limit": limit
    }


@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """按ID获取任意类型报告。"""
    report = db.get_report(user_id, report_id)
    if not report:
        raise HTTPException(404, "报告不存在")
    normalized = _normalize_report_for_api(report)
    normalized["improvementPlan"] = _build_action_plan_for_report(user_id, report)
    return {"ok": True, "report": normalized}


@router.delete("/report/{report_id}")
async def delete_report(
    report_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """删除用户自己的报告。"""
    if not db.delete_report(user_id, report_id):
        raise HTTPException(404, "报告不存在")
    return {"ok": True}


def _resolve_combined_sources(user_id: str, data: CombinedAnalyze) -> List[Dict]:
    """优先使用指定报告ID；未指定时取各类型最新报告。"""
    source_reports: List[Dict] = []
    explicit_ids = [
        ("voice", data.voice_report_id),
        ("face", data.face_report_id),
        ("video", data.video_report_id),
    ]

    for expected_type, report_id in explicit_ids:
        if not report_id:
            continue
        report = db.get_report(user_id, report_id)
        if not report:
            raise HTTPException(404, f"{expected_type}报告不存在")
        if report.get("type") != expected_type:
            raise HTTPException(400, f"{report_id} 不是{expected_type}报告")
        source_reports.append(report)

    existing_types = {report.get("type") for report in source_reports}
    for report_type in ("voice", "face", "video"):
        if report_type in existing_types:
            continue
        latest = db.get_user_reports(user_id, report_type=report_type, limit=1, offset=0)
        if latest:
            source_reports.append(latest[0])

    return source_reports


def _build_combined_report(source_reports: List[Dict]) -> Dict:
    scores = {
        report.get("type", "voice"): float(report.get("overall_score", report.get("score", 0)) or 0)
        for report in source_reports
    }
    weights = {"voice": 0.45, "face": 0.35, "video": 0.20}
    active_weight = sum(weights.get(key, 0.2) for key in scores) or 1
    overall_score = round(sum(scores[key] * weights.get(key, 0.2) for key in scores) / active_weight, 1)

    voice_report = next((r for r in source_reports if r.get("type") == "voice"), None)
    face_report = next((r for r in source_reports if r.get("type") == "face"), None)
    video_report = next((r for r in source_reports if r.get("type") == "video"), None)

    voice_score = scores.get("voice", overall_score)
    face_score = scores.get("face", overall_score)
    video_score = scores.get("video", overall_score)
    aging_score = round((face_score * 0.65 + video_score * 0.35) if ("face" in scores or "video" in scores) else overall_score)

    dimensions = [
        {"name": "心血管", "icon": "❤️", "score": _clamp_score(voice_score - 2 if voice_report else overall_score)},
        {"name": "呼吸系统", "icon": "🫁", "score": _clamp_score(voice_score + 1 if voice_report else overall_score)},
        {"name": "神经系统", "icon": "🧠", "score": _clamp_score((voice_score * 0.7 + overall_score * 0.3) if voice_report else overall_score)},
        {"name": "代谢状态", "icon": "⚖️", "score": _clamp_score((voice_score * 0.4 + face_score * 0.6) if face_report else overall_score)},
        {"name": "免疫压力", "icon": "🛡️", "score": _clamp_score((voice_score + face_score + video_score) / 3)},
        {"name": "衰老程度", "icon": "⏳", "score": _clamp_score(aging_score)},
    ]

    biological_age = _estimate_biological_age(overall_score, face_report, video_report)
    source_names = "、".join(_source_type_name(report.get("type")) for report in source_reports)
    summary = f"已整合{source_names}数据，综合评分 {overall_score} 分。{_score_summary(overall_score)}"

    return {
        "voice_report_id": voice_report.get("id") if voice_report else None,
        "face_report_id": face_report.get("id") if face_report else None,
        "video_report_id": video_report.get("id") if video_report else None,
        "overall_score": overall_score,
        "biological_age": biological_age,
        "dimensions": dimensions,
        "summary": summary,
        "suggestions": _combined_suggestions(overall_score, dimensions),
    }


def _estimate_biological_age(score: float, face_report: Optional[Dict], video_report: Optional[Dict]) -> int:
    age_candidates = []
    if face_report and face_report.get("predicted_age"):
        age_candidates.append(float(face_report["predicted_age"]))
    if video_report and video_report.get("biological_age"):
        age_candidates.append(float(video_report["biological_age"]))
    if age_candidates:
        return int(round(sum(age_candidates) / len(age_candidates)))
    return int(max(18, min(75, round(45 - (score - 70) * 0.35))))


def _combined_suggestions(score: float, dimensions: List[Dict]) -> List[str]:
    weakest = sorted(dimensions, key=lambda item: item["score"])[:2]
    suggestions = [
        "保持规律作息，连续复测时尽量固定在相近时间段采集。",
        "每周进行3-5次中等强度运动，并记录睡眠、饮食和压力变化。",
    ]
    for item in weakest:
        suggestions.append(f"重点关注{item['name']}相关指标，若连续多次低于70分，建议结合体检或咨询专业医生。")
    if score < 70:
        suggestions.append("当前综合评分偏低，建议优先排查近期疲劳、感染、睡眠不足或慢性病管理问题。")
    return suggestions[:5]


def _source_type_name(report_type: str) -> str:
    return {"voice": "声纹", "face": "面部", "video": "视频"}.get(report_type, "检测")


def _score_summary(score: float) -> str:
    if score >= 90:
        return "整体指标优秀，请继续保持当前生活方式。"
    if score >= 80:
        return "整体状态良好，可继续观察趋势变化。"
    if score >= 70:
        return "部分维度需要关注，建议改善睡眠、运动和压力管理。"
    if score >= 60:
        return "健康压力信号增多，建议增加复测并结合线下检查。"
    return "多项指标偏低，本报告仅作提醒，请及时咨询专业医生。"


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _normalize_report_for_api(report: dict) -> dict:
    """给小程序提供稳定字段，同时保留原始字段。"""
    result = dict(report)
    report_type = result.get("type") or "voice"
    score = result.get("overall_score", result.get("score", 0)) or 0

    result["type"] = report_type
    result["analysisType"] = report_type
    result["overallScore"] = round(float(score), 1)
    result["score"] = round(float(score), 1)
    result["createdAt"] = result.get("created_at")

    if report_type == "voice":
        features = result.get("features") or []
        result["acousticFeatures"] = [
            {
                "name": item.get("name", "声学指标"),
                "score": int(item.get("percent") or item.get("score") or 0),
                "value": item.get("value", ""),
                "desc": item.get("desc") or item.get("description") or ""
            }
            for item in features
        ]
        result["voiceDomains"] = result.get("domains") or result.get("voice_domains") or []
        result["voiceQuality"] = result.get("voice_quality") or {}
        result["voiceProfile"] = result.get("feature_vector") or {}

        risks = result.get("risks") or []
        result["riskAssessment"] = [
            {
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "category": item.get("category") or item.get("name", "健康风险"),
                "level": item.get("level", "low"),
                "score": int(item.get("score") or _risk_score(item.get("level", "low"))),
                "levelText": item.get("levelText") or item.get("level_text") or "",
                "desc": item.get("description") or item.get("desc") or "",
                "suggestion": item.get("suggestion", ""),
                "markers": item.get("markers", [])
            }
            for item in risks
        ]

        if result.get("ai_insight"):
            result["aiAdvice"] = [{
                "title": "健康建议",
                "content": result["ai_insight"],
                "icon": "💡"
            }]

    if report_type == "face":
        result["predictedAge"] = result.get("predicted_age")

    if report_type == "video":
        result["biologicalAge"] = result.get("biological_age")
        result["skin"] = result.get("skin") or result.get("skin_result")
        result["eye"] = result.get("eye") or result.get("eye_result")
        result["hair"] = result.get("hair") or result.get("hair_result")

    if report_type == "combined":
        result["biologicalAge"] = result.get("biological_age")
        result["predictedAge"] = result.get("biological_age")
        suggestions = result.get("suggestions") or []
        result["aiAdvice"] = [
            {"title": "综合建议", "content": item, "icon": "💡"}
            for item in suggestions
        ]

    return result


def _risk_score(level: str) -> int:
    return {"low": 25, "medium": 58, "high": 86}.get(level, 30)


# ═══════ 健康数据开放接口（供小程序和未来模块集成） ═══════

def _generated_at() -> str:
    return datetime.now().isoformat()


def _require_user(user_id: str) -> Dict:
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def _validate_public_report_type(report_type: str) -> str:
    if report_type not in PUBLIC_REPORT_TYPES:
        raise HTTPException(400, "报告类型不支持")
    return report_type


def _report_type_name(report_type: str) -> str:
    return {
        "voice": "声纹健康参考",
        "face": "面部状态评估",
        "video": "视频健康观察",
        "combined": "综合健康评估",
        "all": "全部健康数据",
    }.get(report_type, "健康数据")


def _score_level(score: Any) -> str:
    try:
        value = float(score or 0)
    except (TypeError, ValueError):
        return "unknown"
    if value >= 90:
        return "excellent"
    if value >= 80:
        return "good"
    if value >= 70:
        return "watch"
    if value >= 60:
        return "attention"
    return "priority"


def _integration_notice() -> Dict:
    return {
        "positioning": "health_reference",
        "medicalBoundary": "数据用于健康管理、趋势观察和风险提示，不用于确诊、治疗决策或急症分诊。",
        "consent": "对接其他产品前应取得用户对语音、面部、视频和健康参考数据共享的单独授权。",
        "privacy": "建议仅按业务目的请求最小必要字段，默认不输出原始音频、图片、视频文件。",
    }


def _normalize_checkin_date(checkin_date: Optional[str]) -> str:
    if not checkin_date:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        parsed = datetime.strptime(checkin_date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(400, "日期格式应为YYYY-MM-DD") from exc
    return parsed.strftime("%Y-%m-%d")


def _lifestyle_public_summary(summary: Dict) -> Dict:
    return {
        "days": summary.get("days", 0),
        "checkinDays": summary.get("checkinDays", 0),
        "streak": summary.get("streak", 0),
        "avgWaterMl": summary.get("avgWaterMl", 0),
        "exerciseDays": summary.get("exerciseDays", 0),
        "avgExerciseMinutes": summary.get("avgExerciseMinutes", 0),
        "avgSteps": summary.get("avgSteps", 0),
        "avgSleepHours": summary.get("avgSleepHours", 0),
        "avgStressLevel": summary.get("avgStressLevel", 0),
        "latest": summary.get("latest"),
    }


def _build_action_plan_for_report(user_id: str, report: Optional[Dict], days: int = 30) -> Dict:
    lifestyle_summary = _lifestyle_public_summary(db.get_lifestyle_summary(user_id, days=days))
    timeline = _timeline_items(user_id, days, "all")
    if report:
        public_report = _public_health_report(report, include_features=False)
    else:
        stats = db.get_user_stats(user_id)
        public_report = {
            "id": None,
            "type": "overall",
            "typeName": "综合健康参考",
            "score": stats.get("avg_score", 0),
            "scoreLevel": _score_level(stats.get("avg_score", 0)),
            "summary": "基于近期健康记录生成改善方案。",
            "positioning": "health_reference",
        }
    return build_action_plan(public_report, lifestyle_summary=lifestyle_summary, timeline=timeline)


def _days_between(start_date: Optional[str], end_date: Optional[str] = None) -> int:
    if not start_date:
        return 0
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else datetime.now().date()
    except ValueError:
        return 0
    return max(0, (end - start).days)


def _cycle_actions(cycle: Dict) -> List[Dict]:
    return (cycle.get("plan") or {}).get("actions") or []


def _latest_user_score(user_id: str) -> float:
    latest = _get_latest_reports(user_id, "all")
    if not latest:
        return 0
    scores = [float(report.get("overall_score", report.get("score", 0)) or 0) for report in latest]
    return round(sum(scores) / len(scores), 1) if scores else 0


def _cycle_progress_summary(user_id: str, cycle: Dict, progress: List[Dict]) -> Dict:
    actions = _cycle_actions(cycle)
    action_count = len(actions)
    elapsed_days = max(1, _days_between(cycle.get("startDate")) + 1)
    cycle_days = max(1, _days_between(cycle.get("startDate"), cycle.get("targetDate")) or 1)
    elapsed_days = min(elapsed_days, cycle_days)
    completed_units = sum(len(item.get("completedActionIds") or []) for item in progress)
    possible_units = max(1, action_count * elapsed_days)
    completion_rate = round(min(1, completed_units / possible_units) * 100)

    latest_score = _latest_user_score(user_id) or float(cycle.get("latestScore") or cycle.get("baselineScore") or 0)
    baseline = float(cycle.get("baselineScore") or 0)
    target = float(cycle.get("targetScore") or 0)
    score_delta = round(latest_score - baseline, 1)
    days_left = max(0, _days_between(datetime.now().strftime("%Y-%m-%d"), cycle.get("targetDate")))

    today = datetime.now().strftime("%Y-%m-%d")
    today_progress = next((item for item in progress if item.get("checkinDate") == today), None)
    completed_today = set(today_progress.get("completedActionIds") or []) if today_progress else set()
    next_actions = [action for action in actions if action.get("id") not in completed_today][:3]

    if latest_score >= target and completion_rate >= 50:
        loop_status = "improving"
        message = "分数和执行完成度都有改善，可以准备进入下一轮巩固。"
    elif completion_rate < 40:
        loop_status = "needs_consistency"
        message = "当前关键问题是执行不够稳定，建议减少目标数量，先完成最重要的1到2项。"
    elif score_delta < -3:
        loop_status = "needs_review"
        message = "分数没有改善或有下降，建议复查采集质量、近期症状和生活方式变化。"
    else:
        loop_status = "in_progress"
        message = "改善周期进行中，继续完成每日行动并按计划复测。"

    return {
        "actionCount": action_count,
        "progressDays": len(progress),
        "elapsedDays": elapsed_days,
        "cycleDays": cycle_days,
        "daysLeft": days_left,
        "completionRate": completion_rate,
        "completedUnits": completed_units,
        "possibleUnits": possible_units,
        "baselineScore": baseline,
        "latestScore": latest_score,
        "targetScore": target,
        "scoreDelta": score_delta,
        "loopStatus": loop_status,
        "message": message,
        "todayCompletedActionIds": list(completed_today),
        "nextActions": next_actions,
    }


def _cycle_review(user_id: str, cycle: Dict, progress: List[Dict]) -> Dict:
    summary = _cycle_progress_summary(user_id, cycle, progress)
    recommendations = []
    if summary["completionRate"] < 40:
        recommendations.append("先把每日行动压缩到最关键的1到2项，降低执行门槛。")
    if summary["scoreDelta"] >= 5:
        recommendations.append("当前趋势有改善，建议继续执行本周期动作，并在目标日后开启巩固周期。")
    if summary["scoreDelta"] < -3:
        recommendations.append("建议查看是否有熬夜、饮酒、感染、运动过量、录音环境变化等干扰因素。")
    if summary["progressDays"] == 0:
        recommendations.append("还没有执行记录，建议今天先完成一项行动并保存进度。")
    if not recommendations:
        recommendations.append("继续保持当前节奏，并在目标日前后完成一次复测。")

    return {
        "summary": summary,
        "recommendations": recommendations,
        "nextLoop": {
            "shouldAdjust": summary["loopStatus"] in ("needs_consistency", "needs_review"),
            "shouldRecheck": summary["elapsedDays"] >= 7 or summary["scoreDelta"] < -3,
            "canComplete": summary["completionRate"] >= 60 and summary["latestScore"] >= summary["targetScore"],
        },
        "closedLoop": [
            {"step": "detect", "name": "发现问题", "done": True},
            {"step": "plan", "name": "生成方案", "done": True},
            {"step": "act", "name": "每日执行", "done": summary["progressDays"] > 0},
            {"step": "track", "name": "记录饮食运动睡眠压力", "done": db.get_lifestyle_summary(user_id, days=14).get("checkinDays", 0) > 0},
            {"step": "recheck", "name": "复测评分", "done": summary["scoreDelta"] != 0},
            {"step": "adjust", "name": "调整下一轮", "done": summary["loopStatus"] in ("improving", "needs_review", "needs_consistency")},
        ],
    }


def _cycle_payload(user_id: str, cycle: Optional[Dict]) -> Optional[Dict]:
    if not cycle:
        return None
    progress = db.get_improvement_progress(user_id, cycle["id"], limit=90)
    return {
        **cycle,
        "progress": progress,
        "progressSummary": _cycle_progress_summary(user_id, cycle, progress),
        "review": _cycle_review(user_id, cycle, progress),
    }


def _voice_capability_categories() -> Dict[str, List[Dict]]:
    categories: Dict[str, List[Dict]] = {}
    for did, info in DISEASE_REGISTRY.items():
        category = info.get("category", "其他")
        categories.setdefault(category, []).append({
            "id": did,
            "name": info.get("name", did),
            "category": category,
            "description": info.get("description", ""),
            "markers": info.get("markers", []),
        })
    return categories


def _build_capability_catalog() -> Dict:
    evidence = get_evidence_base()
    voice_categories = _voice_capability_categories()
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "product": "VoiceHealth",
        "positioning": "AI声纹与多模态大健康参考平台",
        "reportTypes": [
            {"type": "voice", "name": _report_type_name("voice")},
            {"type": "face", "name": _report_type_name("face")},
            {"type": "video", "name": _report_type_name("video")},
            {"type": "combined", "name": _report_type_name("combined")},
        ],
        "modules": [
            {
                "type": "voice",
                "name": "声音大健康参考",
                "status": "available",
                "itemTotal": len(DISEASE_REGISTRY),
                "categories": voice_categories,
                "featureGroups": ["基频与韵律", "音质稳定性", "能量与响度", "停顿与语速", "频谱与共振峰", "MFCC声纹表示"],
            },
            {
                "type": "face",
                "name": "面部状态评估",
                "status": "available",
                "featureGroups": ["皱纹", "色斑", "紧致度", "眼部状态", "法令纹", "肤色均匀度"],
            },
            {
                "type": "video",
                "name": "视频健康观察",
                "status": "available",
                "featureGroups": ["皮肤状态", "眼部疲劳", "头发状态"],
            },
            {
                "type": "combined",
                "name": "综合健康评估",
                "status": "available",
                "featureGroups": ["声纹", "面部", "视频", "趋势汇总", "综合建议"],
            },
            {
                "type": "lifestyle",
                "name": "每日生活方式打卡",
                "status": "available",
                "featureGroups": ["饮食", "饮水", "运动", "睡眠", "压力", "症状", "备注"],
            },
            {
                "type": "action_plan",
                "name": "健康改善行动计划",
                "status": "available",
                "featureGroups": ["评分解释", "问题信号", "短期目标", "饮食运动睡眠建议", "复测节奏", "就医提醒"],
            },
            {
                "type": "improvement_loop",
                "name": "改善闭环模式",
                "status": "available",
                "featureGroups": ["创建周期", "每日执行", "进度完成度", "复测回顾", "下一轮调整"],
            },
            {
                "type": "evidence_plan_library",
                "name": "循证健康方案库",
                "status": "available",
                "itemTotal": len(get_evidence_health_plans()),
                "featureGroups": ["运动", "饮食", "饮水", "睡眠", "压力", "烟酒", "嗓音", "安全边界"],
            },
        ],
        "evidence": {
            "theoryTotal": len(evidence.get("theories", [])),
            "referenceTotal": len(evidence.get("references", [])),
            "collectionGuideTotal": len(evidence.get("collectionGuide", [])),
            "checkinGuideTotal": len(evidence.get("checkinGuide", [])),
            "endpoint": "/api/v1/evidence",
        },
        "scopes": INTEGRATION_SCOPES,
        "notice": _integration_notice(),
    }


def _integration_manifest() -> Dict:
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "product": {
            "name": "VoiceHealth",
            "description": "语音生物标志物与多模态健康参考平台",
            "apiBase": "/api/v1",
        },
        "auth": {
            "current": "小程序与本地开发阶段使用 X-User-Id 请求头绑定用户数据。",
            "recommendedProduction": "面向第三方模块时使用 API Key/OAuth2 + 用户单独授权 + scope 控制。",
            "requiredHeader": "X-User-Id",
        },
        "scopes": INTEGRATION_SCOPES,
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/v1/integrations/manifest",
                "scope": "health.capability.read",
                "description": "获取集成清单、版本、鉴权和合规边界。",
            },
            {
                "method": "GET",
                "path": "/api/v1/integrations/capabilities",
                "scope": "health.capability.read",
                "description": "获取可对接能力、健康参考项、报告类型和证据概览。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/summary",
                "scope": "health.summary.read",
                "description": "获取用户健康数据总览、各模块数量、最近报告和会员状态。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/latest?type=all",
                "scope": "health.report.read",
                "description": "获取用户最近一次或各模块最近一次健康报告。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/timeline?days=30&type=all",
                "scope": "health.timeline.read",
                "description": "获取可视化趋势时间线。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/export?type=all&limit=50",
                "scope": "health.export.read",
                "description": "导出结构化健康数据包，供其他模块做授权同步。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/action-plan?reportId=<id>",
                "scope": "health.plan.read",
                "description": "根据评分、报告风险信号和生活方式记录生成健康改善行动计划。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-plans",
                "scope": "health.evidence_plan.read",
                "description": "获取循证健康改善方案库。",
            },
            {
                "method": "GET",
                "path": "/api/v1/health-data/evidence-plans?reportId=<id>",
                "scope": "health.evidence_plan.read",
                "description": "根据用户报告和生活方式记录匹配循证健康方案。",
            },
            {
                "method": "POST",
                "path": "/api/v1/improvement/cycles",
                "scope": "health.improvement.write",
                "description": "从最新报告或指定报告创建改善闭环周期。",
            },
            {
                "method": "POST",
                "path": "/api/v1/improvement/cycles/<id>/progress",
                "scope": "health.improvement.write",
                "description": "保存某天改善行动执行进度。",
            },
            {
                "method": "GET",
                "path": "/api/v1/improvement/active",
                "scope": "health.improvement.read",
                "description": "获取当前改善闭环和复测回顾。",
            },
            {
                "method": "POST",
                "path": "/api/v1/lifestyle/checkin",
                "scope": "health.lifestyle.write",
                "description": "保存每日饮食、运动、睡眠、压力和症状记录。",
            },
            {
                "method": "GET",
                "path": "/api/v1/lifestyle/checkins?days=30",
                "scope": "health.lifestyle.read",
                "description": "获取每日生活方式打卡列表。",
            },
        ],
        "notice": _integration_notice(),
    }


def _get_latest_reports(user_id: str, report_type: str) -> List[Dict]:
    types = ("voice", "face", "video", "combined") if report_type == "all" else (report_type,)
    latest_reports: List[Dict] = []
    for item_type in types:
        rows = db.get_user_reports(user_id, report_type=item_type, limit=1, offset=0)
        if rows:
            latest_reports.append(rows[0])
    return latest_reports


def _public_health_report(report: Dict, include_features: bool = False) -> Dict:
    normalized = _normalize_report_for_api(report)
    report_type = normalized.get("type", "voice")
    score = normalized.get("overallScore", normalized.get("score", 0))
    payload: Dict[str, Any] = {
        "id": normalized.get("id"),
        "type": report_type,
        "typeName": _report_type_name(report_type),
        "score": score,
        "scoreLevel": _score_level(score),
        "summary": normalized.get("summary", ""),
        "createdAt": normalized.get("createdAt") or normalized.get("created_at"),
        "positioning": "health_reference",
    }

    if report_type == "voice":
        risks = normalized.get("riskAssessment", [])
        payload["dimensions"] = normalized.get("voiceDomains", [])
        payload["signals"] = [
            {
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "category": item.get("category", ""),
                "level": item.get("level", "low"),
                "score": item.get("score", 0),
                "markers": item.get("markers", []),
                "suggestion": item.get("suggestion", ""),
            }
            for item in risks
        ]
        payload["quality"] = normalized.get("voiceQuality", {})
        if include_features:
            payload["features"] = normalized.get("acousticFeatures", [])

    if report_type == "face":
        payload["predictedAge"] = normalized.get("predictedAge")
        payload["dimensions"] = normalized.get("dimensions", [])
        payload["suggestions"] = normalized.get("suggestions", [])

    if report_type == "video":
        payload["biologicalAge"] = normalized.get("biologicalAge")
        payload["detectItems"] = normalized.get("detect_items", [])
        payload["observations"] = {
            "skin": normalized.get("skin"),
            "eye": normalized.get("eye"),
            "hair": normalized.get("hair"),
        }

    if report_type == "combined":
        payload["biologicalAge"] = normalized.get("biologicalAge")
        payload["dimensions"] = normalized.get("dimensions", [])
        payload["sourceReportIds"] = {
            "voice": normalized.get("voice_report_id"),
            "face": normalized.get("face_report_id"),
            "video": normalized.get("video_report_id"),
        }
        payload["suggestions"] = normalized.get("suggestions", [])

    return payload


def _timeline_items(user_id: str, days: int, report_type: str) -> List[Dict]:
    trends = db.get_trend_data(user_id, days)
    if report_type != "all":
        trends = [item for item in trends if item.get("type") == report_type]
    return [
        {
            "date": item.get("date"),
            "type": item.get("type"),
            "typeName": _report_type_name(item.get("type", "")),
            "score": item.get("score"),
            "scoreLevel": _score_level(item.get("score")),
            "event": "report_created",
        }
        for item in trends
    ]


def _module_status(stats: Dict, latest_reports: List[Dict]) -> List[Dict]:
    latest_by_type = {report.get("type"): report for report in latest_reports}
    modules = []
    for report_type in ("voice", "face", "video", "combined"):
        latest = latest_by_type.get(report_type)
        count = stats.get(f"{report_type}_count", 0)
        latest_score = latest.get("overall_score", latest.get("score")) if latest else None
        modules.append({
            "type": report_type,
            "name": _report_type_name(report_type),
            "enabled": True,
            "reportCount": count,
            "latestReportId": latest.get("id") if latest else None,
            "latestScore": latest_score,
            "latestScoreLevel": _score_level(latest_score) if latest else None,
            "latestAt": latest.get("created_at") if latest else None,
        })
    return modules


@router.get("/integrations/manifest")
async def get_integration_manifest():
    """获取未来对接其他产品/模块的API集成清单。"""
    return _integration_manifest()


@router.get("/integrations/capabilities")
async def get_integration_capabilities():
    """获取平台能力目录、健康参考项、证据概览和数据scope。"""
    return _build_capability_catalog()


@router.get("/health-data/summary")
async def get_health_data_summary(user_id: str = Header(..., alias="X-User-Id")):
    """用户健康数据总览，供小程序首页、个人中心或外部模块使用。"""
    _require_user(user_id)
    stats = db.get_user_stats(user_id)
    latest_reports = _get_latest_reports(user_id, "all")
    lifestyle_summary = db.get_lifestyle_summary(user_id, days=30)
    active_cycle = _cycle_payload(user_id, db.get_active_improvement_cycle(user_id))
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "userId": user_id,
        "summary": {
            "totalReports": stats.get("total_reports", 0),
            "averageScore": stats.get("avg_score", 0),
            "bestScore": stats.get("best_score", 0),
            "freeRemaining": stats.get("free_remaining", 0),
            "isVip": stats.get("is_vip", False),
            "vipExpireAt": stats.get("vip_expire_at"),
        },
        "modules": _module_status(stats, latest_reports),
        "lifestyle": _lifestyle_public_summary(lifestyle_summary),
        "improvement": {
            "hasActiveCycle": bool(active_cycle),
            "activeCycle": active_cycle,
        },
        "latestReports": [_public_health_report(report) for report in latest_reports],
        "notice": _integration_notice(),
    }


@router.get("/health-data/latest")
async def get_latest_health_data(
    user_id: str = Header(..., alias="X-User-Id"),
    report_type: str = Query(default="all", alias="type"),
    include_features: bool = Query(default=False, alias="includeFeatures")
):
    """获取最近报告。type=all时返回各模块最新一份。"""
    _require_user(user_id)
    report_type = _validate_public_report_type(report_type)
    latest_reports = _get_latest_reports(user_id, report_type)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "userId": user_id,
        "type": report_type,
        "reports": [
            _public_health_report(report, include_features=include_features)
            for report in latest_reports
        ],
        "notice": _integration_notice(),
    }


@router.get("/health-data/timeline")
async def get_health_data_timeline(
    user_id: str = Header(..., alias="X-User-Id"),
    days: int = Query(default=30, ge=1, le=365),
    report_type: str = Query(default="all", alias="type")
):
    """获取趋势时间线，适合接入图表、打卡、干预模块。"""
    _require_user(user_id)
    report_type = _validate_public_report_type(report_type)
    timeline = _timeline_items(user_id, days, report_type)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "userId": user_id,
        "type": report_type,
        "days": days,
        "timeline": timeline,
        "total": len(timeline),
        "notice": _integration_notice(),
    }


@router.get("/health-data/action-plan")
async def get_health_action_plan(
    user_id: str = Header(..., alias="X-User-Id"),
    report_id: Optional[str] = Query(default=None, alias="reportId"),
    days: int = Query(default=30, ge=1, le=365)
):
    """根据报告评分、风险信号和生活方式记录生成健康改善方案。"""
    _require_user(user_id)
    report = None
    if report_id:
        report = db.get_report(user_id, report_id)
        if not report:
            raise HTTPException(404, "报告不存在")
    else:
        latest = _get_latest_reports(user_id, "all")
        report = latest[0] if latest else None

    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "reportId": report.get("id") if report else None,
        "actionPlan": _build_action_plan_for_report(user_id, report, days=days),
        "notice": _integration_notice(),
    }


@router.get("/health-plans")
async def list_evidence_health_plans(domain: str = Query(default="all")):
    """获取循证健康改善方案库。"""
    plans = get_evidence_health_plans(domain=domain)
    domains = sorted({plan.get("domain", "其他") for plan in get_evidence_health_plans()})
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "domains": ["all"] + domains,
        "plans": plans,
        "total": len(plans),
        "notice": _integration_notice(),
    }


@router.get("/health-plans/{plan_id}")
async def get_evidence_health_plan_detail(plan_id: str):
    """获取单个循证健康改善方案。"""
    plan = get_evidence_health_plan(plan_id)
    if not plan:
        raise HTTPException(404, "方案不存在")
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "plan": plan,
        "notice": _integration_notice(),
    }


@router.get("/health-data/evidence-plans")
async def match_user_evidence_health_plans(
    user_id: str = Header(..., alias="X-User-Id"),
    report_id: Optional[str] = Query(default=None, alias="reportId"),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=8, ge=1, le=20)
):
    """根据用户报告、分数、风险信号和生活方式记录匹配循证方案。"""
    _require_user(user_id)
    report = None
    if report_id:
        report = db.get_report(user_id, report_id)
        if not report:
            raise HTTPException(404, "报告不存在")
    else:
        latest = _get_latest_reports(user_id, "all")
        report = latest[0] if latest else None

    public_report = _public_health_report(report, include_features=False) if report else {}
    lifestyle_summary = _lifestyle_public_summary(db.get_lifestyle_summary(user_id, days=days))
    plans = match_evidence_health_plans(public_report, lifestyle_summary, limit=limit)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "reportId": report.get("id") if report else None,
        "lifestyle": lifestyle_summary,
        "plans": plans,
        "total": len(plans),
        "notice": _integration_notice(),
    }


# ═══════ 改善闭环模式 ═══════

@router.post("/improvement/cycles")
async def create_improvement_cycle(
    data: ImprovementCycleCreate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """从指定报告或最新报告创建改善闭环周期。"""
    _require_user(user_id)
    report = None
    if data.reportId:
        report = db.get_report(user_id, data.reportId)
        if not report:
            raise HTTPException(404, "报告不存在")
    else:
        latest = _get_latest_reports(user_id, "all")
        report = latest[0] if latest else None

    if not report:
        raise HTTPException(400, "请先完成至少一次健康评估，再开启改善闭环")

    days = max(3, min(60, int(data.days or 14)))
    plan = _build_action_plan_for_report(user_id, report, days=30)
    cycle = db.create_improvement_cycle(
        user_id,
        plan,
        source_report_id=report.get("id"),
        duration_days=days,
    )
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "cycle": _cycle_payload(user_id, cycle),
        "notice": _integration_notice(),
    }


@router.get("/improvement/active")
async def get_active_improvement_cycle(
    user_id: str = Header(..., alias="X-User-Id"),
    auto_create: bool = Query(default=False, alias="autoCreate")
):
    """获取当前改善闭环；autoCreate=true时可从最新报告自动创建。"""
    _require_user(user_id)
    cycle = db.get_active_improvement_cycle(user_id)
    created = False
    if not cycle and auto_create:
        latest = _get_latest_reports(user_id, "all")
        if latest:
            plan = _build_action_plan_for_report(user_id, latest[0], days=30)
            cycle = db.create_improvement_cycle(user_id, plan, source_report_id=latest[0].get("id"), duration_days=14)
            created = True

    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "created": created,
        "cycle": _cycle_payload(user_id, cycle),
        "notice": _integration_notice(),
    }


@router.get("/improvement/cycles")
async def list_improvement_cycles(
    user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """列出历史改善闭环周期。"""
    _require_user(user_id)
    cycles = db.list_improvement_cycles(user_id, limit=limit)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "cycles": [_cycle_payload(user_id, cycle) for cycle in cycles],
        "total": len(cycles),
    }


@router.get("/improvement/cycles/{cycle_id}")
async def get_improvement_cycle(
    cycle_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取改善闭环周期详情。"""
    _require_user(user_id)
    cycle = db.get_improvement_cycle(user_id, cycle_id)
    if not cycle:
        raise HTTPException(404, "改善周期不存在")
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "cycle": _cycle_payload(user_id, cycle),
    }


@router.post("/improvement/cycles/{cycle_id}/progress")
async def save_improvement_progress(
    cycle_id: str,
    data: ImprovementProgressUpdate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """保存某一天的改善行动完成情况。"""
    _require_user(user_id)
    cycle = db.get_improvement_cycle(user_id, cycle_id)
    if not cycle:
        raise HTTPException(404, "改善周期不存在")
    if cycle.get("status") != "active":
        raise HTTPException(400, "该改善周期不是进行中状态")

    payload = data.dict()
    payload["checkinDate"] = _normalize_checkin_date(payload.get("checkinDate"))
    if payload["moodScore"] < 0 or payload["moodScore"] > 5:
        raise HTTPException(400, "心情评分应在0到5之间")
    if payload["energyScore"] < 0 or payload["energyScore"] > 5:
        raise HTTPException(400, "精力评分应在0到5之间")

    progress = db.save_improvement_progress(user_id, cycle_id, payload)
    refreshed = db.get_improvement_cycle(user_id, cycle_id)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "progress": progress,
        "cycle": _cycle_payload(user_id, refreshed),
        "notice": _integration_notice(),
    }


@router.get("/improvement/cycles/{cycle_id}/review")
async def get_improvement_cycle_review(
    cycle_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """获取改善闭环复盘：完成度、分数变化、下一步建议。"""
    _require_user(user_id)
    cycle = db.get_improvement_cycle(user_id, cycle_id)
    if not cycle:
        raise HTTPException(404, "改善周期不存在")
    progress = db.get_improvement_progress(user_id, cycle_id, limit=90)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "cycleId": cycle_id,
        "review": _cycle_review(user_id, cycle, progress),
    }


@router.post("/improvement/cycles/{cycle_id}/status")
async def update_improvement_cycle_status(
    cycle_id: str,
    data: ImprovementCycleStatusUpdate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """完成、暂停或取消改善周期。"""
    _require_user(user_id)
    if data.status not in ("active", "paused", "completed", "cancelled"):
        raise HTTPException(400, "状态不支持")
    latest_score = _latest_user_score(user_id)
    cycle = db.update_improvement_cycle_status(user_id, cycle_id, data.status, latest_score=latest_score)
    if not cycle:
        raise HTTPException(404, "改善周期不存在")
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "cycle": _cycle_payload(user_id, cycle),
        "notice": _integration_notice(),
    }


@router.get("/health-data/export")
async def export_health_data(
    user_id: str = Header(..., alias="X-User-Id"),
    report_type: str = Query(default="all", alias="type"),
    limit: int = Query(default=50, ge=1, le=200),
    days: int = Query(default=365, ge=1, le=3650),
    include_features: bool = Query(default=False, alias="includeFeatures")
):
    """导出结构化健康数据包，供用户授权后的跨模块同步使用。"""
    _require_user(user_id)
    report_type = _validate_public_report_type(report_type)
    reports = db.get_user_reports(user_id, report_type=report_type, limit=limit, offset=0)
    stats = db.get_user_stats(user_id)
    timeline = _timeline_items(user_id, days, report_type)
    lifestyle_records = db.get_lifestyle_checkins(user_id, days=days, limit=limit)
    lifestyle_summary = db.get_lifestyle_summary(user_id, days=min(days, 365))
    action_plan = _build_action_plan_for_report(user_id, reports[0] if reports else None, days=min(days, 365))
    improvement_cycles = db.list_improvement_cycles(user_id, limit=min(limit, 20))
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "package": {
            "ownerUserId": user_id,
            "type": report_type,
            "reportCount": len(reports),
            "timelineCount": len(timeline),
            "limit": limit,
            "days": days,
        },
        "stats": {
            "totalReports": stats.get("total_reports", 0),
            "averageScore": stats.get("avg_score", 0),
            "bestScore": stats.get("best_score", 0),
        },
        "reports": [
            _public_health_report(report, include_features=include_features)
            for report in reports
        ],
        "timeline": timeline,
        "lifestyle": {
            "summary": _lifestyle_public_summary(lifestyle_summary),
            "records": lifestyle_records,
        },
        "actionPlan": action_plan,
        "evidencePlans": action_plan.get("evidencePlans", []),
        "improvement": {
            "cycles": [_cycle_payload(user_id, cycle) for cycle in improvement_cycles],
            "activeCycleId": (db.get_active_improvement_cycle(user_id) or {}).get("id"),
        },
        "capabilities": {
            "endpoint": "/api/v1/integrations/capabilities",
            "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
            "voiceHealthItemTotal": len(DISEASE_REGISTRY),
        },
        "notice": _integration_notice(),
    }


# ═══════ 每日饮食/运动/生活方式打卡 ═══════

@router.post("/lifestyle/checkin")
async def save_lifestyle_checkin(
    data: LifestyleCheckin,
    user_id: str = Header(..., alias="X-User-Id")
):
    """保存或更新用户每日饮食、运动、睡眠、压力和症状记录。"""
    _require_user(user_id)
    payload = data.dict()
    payload["checkinDate"] = _normalize_checkin_date(payload.get("checkinDate"))

    if payload["waterMl"] < 0 or payload["exerciseMinutes"] < 0 or payload["steps"] < 0:
        raise HTTPException(400, "饮水、运动时长和步数不能为负数")
    if payload["sleepHours"] < 0 or payload["sleepHours"] > 24:
        raise HTTPException(400, "睡眠时长应在0到24小时之间")
    if payload["stressLevel"] < 0 or payload["stressLevel"] > 5:
        raise HTTPException(400, "压力等级应在0到5之间")

    checkin = db.save_lifestyle_checkin(user_id, payload)
    summary = db.get_lifestyle_summary(user_id, days=30)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "checkin": checkin,
        "summary": _lifestyle_public_summary(summary),
        "notice": _integration_notice(),
    }


@router.get("/lifestyle/checkin")
async def get_lifestyle_checkin(
    user_id: str = Header(..., alias="X-User-Id"),
    checkin_date: Optional[str] = Query(default=None, alias="date")
):
    """获取某一天的生活方式打卡。"""
    _require_user(user_id)
    normalized_date = _normalize_checkin_date(checkin_date)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "date": normalized_date,
        "checkin": db.get_lifestyle_checkin(user_id, normalized_date),
    }


@router.get("/lifestyle/checkins")
async def list_lifestyle_checkins(
    user_id: str = Header(..., alias="X-User-Id"),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=365)
):
    """获取生活方式打卡列表。"""
    _require_user(user_id)
    records = db.get_lifestyle_checkins(user_id, days=days, limit=limit)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "days": days,
        "records": records,
        "total": len(records),
    }


@router.get("/lifestyle/summary")
async def get_lifestyle_summary(
    user_id: str = Header(..., alias="X-User-Id"),
    days: int = Query(default=30, ge=1, le=365)
):
    """获取饮食、运动、睡眠和压力打卡汇总。"""
    _require_user(user_id)
    summary = db.get_lifestyle_summary(user_id, days=days)
    return {
        "ok": True,
        "schemaVersion": HEALTH_DATA_SCHEMA_VERSION,
        "generatedAt": _generated_at(),
        "summary": _lifestyle_public_summary(summary),
        "notice": _integration_notice(),
    }


# ═══════ 统计趋势 ═══════

@router.get("/stats")
async def get_stats(user_id: str = Header(..., alias="X-User-Id")):
    """获取用户统计"""
    stats = db.get_user_stats(user_id)
    return {"ok": True, "stats": stats}

@router.get("/trends")
async def get_trends(
    user_id: str = Header(..., alias="X-User-Id"),
    days: int = Query(default=30, le=365)
):
    """获取趋势数据"""
    trends = db.get_trend_data(user_id, days)
    return {"ok": True, "trends": trends}


# ═══════ 订单支付 ═══════

@router.post("/order/create")
async def create_order(
    data: OrderCreate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """创建订单"""
    order = db.create_order(user_id, data.type, data.amount)
    return {
        "ok": True,
        "order": order,
        "payment": {
            "timeStamp": str(int(datetime.now().timestamp())),
            "nonceStr": os.urandom(16).hex(),
            "package": f"prepay_id={order['order_no']}",
            "signType": "MD5",
            "paySign": "mock_sign"
        }
    }

@router.post("/order/callback")
async def order_callback(data: OrderCallback):
    """支付回调"""
    order = db.get_order_by_no(data.order_no)
    if not order:
        raise HTTPException(404, "订单不存在")
    
    # 更新订单状态
    db.update_order_status(order['id'], data.status, data.payment_id)
    
    # 如果支付成功，激活VIP
    if data.status == 'paid':
        if order['type'] == 'vip_monthly':
            db.activate_vip(order['user_id'], order['id'], days=30)
    
    return {"ok": True}

@router.get("/order/list")
async def get_orders(
    user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(default=20)
):
    """获取订单列表"""
    conn = db.get_conn()
    rows = conn.execute('''
        SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit)).fetchall()
    conn.close()
    return {"ok": True, "orders": [dict(r) for r in rows]}


# ═══════ 验证接口 ═══════

@router.get("/verification/text")
async def get_reading_text():
    """获取朗读文本"""
    import random
    text = random.choice(READING_TEXTS)
    return {"ok": True, "text": text}

@router.post("/verification/liveness")
async def check_liveness(audio: UploadFile = File(...)):
    """活体检测"""
    suffix = Path(audio.filename or "audio.wav").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = liveness_detector.detect(tmp_path)
        os.unlink(tmp_path)
        return {
            "ok": True,
            "is_live": result.is_live,
            "score": result.score,
            "checks": result.checks
        }
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(500, str(e))


# ═══════ 声音健康参考项 ═══════

@router.get("/diseases")
async def list_diseases():
    """获取声音健康参考项列表"""
    categories = {}
    for did, info in DISEASE_REGISTRY.items():
        cat = info.get('category', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'id': did,
            'name': info['name'],
            'description': info.get('description', ''),
            'markers': info.get('markers', [])
        })
    return {"ok": True, "total": len(DISEASE_REGISTRY), "categories": categories}


# ═══════ 理论基础与参考指南 ═══════

@router.get("/evidence")
async def get_evidence():
    """获取平台理论基础、参考文献、采集指南、打卡指南和合规说明。"""
    return get_evidence_base()


# ═══════ 健康检查 ═══════

@router.get("/health")
async def health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "service": "VoiceHealth",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "diseases": len(DISEASE_REGISTRY)
    }
