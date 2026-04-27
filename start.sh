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
MINIPROGRAM_DIR="$PROJECT_DIR/../voiceHealth-miniprogram"

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
python3.12 src/api.main &
BACKEND_PID=$!
echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo -e "${GREEN}API地址: http://localhost:8100${NC}"

sleep 2

echo -e "${BLUE}[4/4] 检查服务状态...${NC}"
if curl -s http://localhost:8100/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常运行${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务启动中...${NC}"
fi

echo ""
echo "=== 启动完成 ==="
echo ""
echo "后端API: http://localhost:8100"
echo "API文档: http://localhost:8100/docs"
echo "测试页面: http://localhost:8100/test"
echo ""
echo "小程序开发:"
echo "  1. 打开微信开发者工具"
echo "  2. 导入项目: $MINIPROGRAM_DIR"
echo "  3. 配置云开发环境"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待后端进程
wait $BACKEND_PID
