"""
VoiceHealth - FastAPI入口
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.routes import router
from src.core.disease_detector import DISEASE_REGISTRY, DiseaseDetector
from src.core.feature_extractor import FeatureExtractor

app = FastAPI(
    title="VoiceHealth",
    description="Voice Biomarker AI Platform - 30s Voice, Health Reference Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-User-Id"],
)

app.include_router(router)

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
extractor = FeatureExtractor(sr=16000)
detector = DiseaseDetector()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the static product page when present, otherwise API landing text."""
    for path in (DOCS_DIR / "index.html", FRONTEND_DIR / "index.html"):
        if path.exists():
            return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>VoiceHealth API v1.0</h1><p>访问 <a href='/docs'>/docs</a> 查看API文档</p>")


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """完整测试页面"""
    test_path = Path(__file__).parent.parent.parent / "frontend" / "test.html"
    if test_path.exists():
        return HTMLResponse(content=test_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Test page not found</h1>")


@app.get("/api/health")
async def health_check_compat():
    """Compatibility health endpoint for older web builds."""
    return {
        "status": "healthy",
        "service": "VoiceHealth",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "diseases": len(DISEASE_REGISTRY),
    }


@app.get("/api/diseases")
async def diseases_compat():
    """Compatibility disease/reference catalog endpoint."""
    categories = {}
    for did, info in DISEASE_REGISTRY.items():
        cat = info["category"]
        categories.setdefault(cat, []).append({
            "id": did,
            "name": info["name"],
            "markers": info["markers"],
            "description": info["description"],
        })
    return {"ok": True, "total": len(DISEASE_REGISTRY), "categories": categories}


@app.post("/api/analyze")
async def analyze_compat(audio: UploadFile = File(...)):
    """Compatibility voice analysis endpoint without user persistence."""
    suffix = Path(audio.filename or "audio.wav").suffix.lower()
    if suffix not in (".wav", ".mp3", ".ogg", ".webm", ".m4a", ".flac"):
        raise HTTPException(400, f"不支持的格式: {suffix}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        features = extractor.extract(tmp_path)
        report = detector.generate_report(features)
        return {
            "ok": True,
            "timestamp": datetime.now().isoformat(),
            "report": report.to_dict(),
            "features": features.to_dict(),
            "notice": "本接口用于兼容旧版演示，不保存用户记录；生产小程序请使用 /api/v1/voice/analyze。",
        }
    except Exception as exc:
        raise HTTPException(500, f"分析失败: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VOICEHEALTH_PORT", "8100"))
    host = os.getenv("VOICEHEALTH_HOST", "0.0.0.0")
    print(f"[VoiceHealth] Starting on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
