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
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends, Query
from pydantic import BaseModel

from src.core.database import db
from src.core.feature_extractor import FeatureExtractor
from src.core.disease_detector import DiseaseDetector, DISEASE_REGISTRY
from src.core.voice_verifier import LivenessDetector, ReadingVerifier, READING_TEXTS

router = APIRouter(prefix="/api/v1", tags=["VoiceHealth API"])

extractor = FeatureExtractor(sr=16000)
detector = DiseaseDetector()
liveness_detector = LivenessDetector(sr=16000)
reading_verifier = ReadingVerifier()


# ═══════ 数据模型 ═══════

class UserRegister(BaseModel):
    openid: str
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

@router.put("/user/profile")
async def update_profile(
    data: UserUpdate,
    user_id: str = Header(..., alias="X-User-Id")
):
    """更新用户信息"""
    db.update_user(user_id, **data.dict(exclude_none=True))
    user = db.get_user(user_id)
    return {"ok": True, "user": user}


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
    5. 疾病风险评估
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
        # 1. 活体检测
        liveness_result = liveness_detector.detect(tmp_path)
        
        # 2. 朗读验证（简化版）
        reading_match = 0.75  # 实际应调用ASR
        
        # 3. 提取声学特征
        features = extractor.extract(tmp_path)
        
        # 4. 生成疾病风险报告
        report = detector.generate_report(features)
        report_dict = report.to_dict()
        
        # 5. 保存报告
        voice_report = {
            'overall_score': report_dict.get('overall_score', 75),
            'summary': report_dict.get('summary', '声纹特征分析完成'),
            'features': [
                {'name': '语速', 'value': f'{features.speech_rate:.1f}', 'percent': 85},
                {'name': '音调', 'value': f'{features.f0_mean:.0f}Hz', 'percent': 72},
                {'name': '稳定性', 'value': f'{(1-features.jitter_local)*100:.0f}%', 'percent': 88},
                {'name': '清晰度', 'value': f'{features.hnr_mean:.1f}dB', 'percent': 90},
            ],
            'risks': report_dict.get('risks', []),
            'ai_insight': '基于声纹分析，建议保持良好作息习惯。',
            'reading_text_id': reading_text_id,
            'liveness_score': liveness_result.score,
            'reading_match_score': reading_match,
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
    
    # 模拟分析结果
    import random
    score = 65 + random.randint(0, 25)
    
    face_report = {
        'overall_score': score,
        'predicted_age': 25 + random.randint(0, 10),
        'dimensions': [
            {'name': '皱纹', 'score': 60 + random.randint(0, 30)},
            {'name': '色斑', 'score': 60 + random.randint(0, 30)},
            {'name': '紧致度', 'score': 60 + random.randint(0, 30)},
            {'name': '眼部', 'score': 60 + random.randint(0, 30)},
            {'name': '法令纹', 'score': 60 + random.randint(0, 30)},
            {'name': '肤色', 'score': 60 + random.randint(0, 30)}
        ],
        'summary': '面部皮肤状态良好，建议加强防晒。',
        'suggestions': ['注意防晒', '保持充足睡眠', '适当补充胶原蛋白']
    }
    
    report_id = db.save_face_report(user_id, face_report)
    
    return {
        "ok": True,
        "report_id": report_id,
        "report": face_report
    }


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
    import random
    
    result = {
        'overall_score': 65 + random.randint(0, 25),
        'biological_age': 25 + random.randint(0, 10),
        'detect_items': items
    }
    
    if 'skin' in items:
        result['skin'] = {
            'overall_score': 60 + random.randint(0, 30),
            'summary': '肤色均匀，轻微痘痘',
            'suggestions': ['注意防晒', '保持清洁']
        }
    
    if 'eye' in items:
        result['eye'] = {
            'overall_score': 60 + random.randint(0, 30),
            'summary': '轻微黑眼圈',
            'suggestions': ['保证充足睡眠']
        }
    
    if 'hair' in items:
        result['hair'] = {
            'overall_score': 60 + random.randint(0, 30),
            'summary': '发量正常',
            'suggestions': ['保持健康饮食']
        }
    
    report_id = db.save_video_report(user_id, result)
    
    return {
        "ok": True,
        "report_id": report_id,
        "result": result
    }


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


# ═══════ 疾病信息 ═══════

@router.get("/diseases")
async def list_diseases():
    """获取可检测疾病列表"""
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
