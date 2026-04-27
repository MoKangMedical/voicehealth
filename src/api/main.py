"""
VoiceHealth - FastAPI入口
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.routes import router

app = FastAPI(
    title="VoiceHealth",
    description="AI声纹健康检测系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/", response_class=HTMLResponse)
async def index():
    return "<h1>VoiceHealth API v1.0</h1><p>访问 <a href='/docs'>/docs</a> 查看API文档</p>"

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return "<h1>VoiceHealth 测试页面</h1>"

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VOICEHEALTH_PORT", "8100"))
    print(f"[VoiceHealth] Starting on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
