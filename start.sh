#!/bin/bash
# VoiceHealth 启动脚本

echo "=== VoiceHealth 闭环系统启动 ==="

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目路径
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR"
MINIPROGRAM_DIR="$PROJECT_DIR/voiceHealth-miniprogram-v2"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

PORT="${VOICEHEALTH_PORT:-8100}"

echo -e "${BLUE}[1/4] 检查环境...${NC}"

# 检查Python
if ! command -v python3.12 &> /dev/null; then
    echo -e "${YELLOW}Python 3.12 未安装${NC}"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3.12 -m venv "$BACKEND_DIR/venv"
    source "$BACKEND_DIR/venv/bin/activate"
    pip install -r "$BACKEND_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
else
    source "$BACKEND_DIR/venv/bin/activate"
fi

echo -e "${GREEN}环境检查完成${NC}"

echo -e "${BLUE}[2/4] 初始化数据库...${NC}"
python3.12 -c "
from src.core.database import db
print('数据库初始化完成')
"

echo -e "${BLUE}[3/4] 启动后端服务...${NC}"
cd "$BACKEND_DIR"
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo -e "${YELLOW}端口 $PORT 已有服务监听，跳过重复启动${NC}"
    BACKEND_PID=""
else
    python3.12 src/api/main.py &
    BACKEND_PID=$!
fi
if [ -n "$BACKEND_PID" ]; then
    echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
fi
echo -e "${GREEN}API地址: http://127.0.0.1:$PORT${NC}"

sleep 2

echo -e "${BLUE}[4/4] 检查服务状态...${NC}"
if curl -s "http://127.0.0.1:$PORT/api/v1/health" > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常运行${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务启动中...${NC}"
fi

echo ""
echo "=== 启动完成 ==="
echo ""
echo "后端API: http://127.0.0.1:$PORT"
echo "API文档: http://127.0.0.1:$PORT/docs"
echo "测试页面: http://127.0.0.1:$PORT/test"
echo ""
echo "小程序开发:"
echo "  1. 打开微信开发者工具"
echo "  2. 导入项目: $MINIPROGRAM_DIR"
echo "  3. 本地模拟器使用 http://127.0.0.1:$PORT"
echo "  4. 真机调试把 miniprogram/config.js 的 devBaseUrl 改为电脑局域网 IP"
echo ""
if [ -n "$BACKEND_PID" ]; then
    echo "按 Ctrl+C 停止服务"
else
    echo "已有服务在运行；如需停止 launchctl 服务：launchctl remove voicehealth-api"
fi
echo ""

# 等待后端进程
if [ -n "$BACKEND_PID" ]; then
    wait "$BACKEND_PID"
fi
