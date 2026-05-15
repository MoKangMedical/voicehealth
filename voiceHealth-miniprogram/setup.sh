#!/bin/bash
# VoiceHealth 一键配置脚本

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       VoiceHealth 一键配置脚本                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}使用方式: ./setup.sh <APPID> [CLOUD_ENV]${NC}"
    echo ""
    echo "示例: ./setup.sh wx1234567890abcdef voicehealth-prod"
    echo ""
    echo "参数说明:"
    echo "  APPID      - 微信小程序AppID (必填)"
    echo "  CLOUD_ENV  - 云开发环境ID (可选，默认自动创建)"
    echo ""
    exit 1
fi

APPID=$1
CLOUD_ENV=${2:-"voicehealth-$(date +%s)"}

echo -e "${BLUE}[1/5] 配置小程序AppID...${NC}"

# 更新 project.config.json
cd ~/Desktop/voiceHealth-miniprogram
python3.12 -c "
import json
with open('project.config.json') as f:
    cfg = json.load(f)
cfg['appid'] = '$APPID'
with open('project.config.json', 'w') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print('✓ project.config.json AppID已更新')
"

echo -e "${GREEN}  AppID: $APPID${NC}"

echo ""
echo -e "${BLUE}[2/5] 配置云开发环境...${NC}"

# 更新 config.js
python3.12 -c "
with open('miniprogram/config.js') as f:
    content = f.read()
content = content.replace(\"voicehealth-xxxxx\", \"$CLOUD_ENV\")
with open('miniprogram/config.js', 'w') as f:
    f.write(content)
print('✓ config.js 云环境ID已更新')
"

echo -e "${GREEN}  云环境: $CLOUD_ENV${NC}"

echo ""
echo -e "${BLUE}[3/5] 检查后端服务...${NC}"

if curl -s http://localhost:8100/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ 后端服务运行中${NC}"
else
    echo -e "${YELLOW}  ⚠ 后端服务未运行，正在启动...${NC}"
    cd ~/Desktop/voiceHealth
    source venv/bin/activate
    nohup python3.12 src/api.main > /tmp/voicehealth.log 2>&1 &
    sleep 3
    if curl -s http://localhost:8100/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ 后端服务已启动${NC}"
    else
        echo -e "${RED}  ✗ 后端服务启动失败，请手动检查${NC}"
    fi
fi

echo ""
echo -e "${BLUE}[4/5] 生成部署清单...${NC}"

cat > ~/Desktop/voiceHealth-miniprogram/DEPLOY.md << 'EOF'
# VoiceHealth 部署清单

## 微信开发者工具配置

1. **导入项目**
   - 打开微信开发者工具
   - 选择「导入项目」
   - 目录: ~/Desktop/voiceHealth-miniprogram
   - AppID: [已配置]

2. **开通云开发**
   - 点击工具栏「云开发」按钮
   - 首次使用需要开通
   - 获取云环境ID

3. **部署云函数**
   - 右键 cloudfunctions 目录
   - 选择「上传并部署：云端安装依赖」
   - 依次部署: analyze, face-analyze, payment, payment-callback, verify, video-analyze

4. **创建数据库集合**
   - 在云开发控制台创建:
     - reports (语音报告)
     - face_reports (面部报告)
     - video_reports (视频报告)
     - orders (订单)
     - vip_records (VIP记录)
     - verification_logs (验证日志)

5. **配置合法域名**
   - 小程序后台 → 开发管理 → 开发设置 → 服务器域名
   - request合法域名: [你的后端API地址]
   - uploadFile合法域名: [你的后端API地址]

## 测试流程

1. 模拟器测试所有页面
2. 真机预览测试
3. 录音功能测试
4. 支付流程测试

## 提交审核

1. 点击「上传」按钮
2. 版本号: 1.0.0
3. 项目备注: VoiceHealth v1.0.0 首次发布
4. 登录 mp.weixin.qq.com
5. 版本管理 → 提交审核
6. 填写审核信息
EOF

echo -e "${GREEN}  ✓ 部署清单已生成: DEPLOY.md${NC}"

echo ""
echo -e "${BLUE}[5/5] 验证配置...${NC}"

# 验证配置
python3.12 -c "
import json
with open('project.config.json') as f:
    cfg = json.load(f)
print(f'  AppID: {cfg[\"appid\"]}')

with open('miniprogram/config.js') as f:
    content = f.read()
    import re
    env = re.search(r\"cloudEnv:'([^']+)'\", content)
    if env:
        print(f'  云环境: {env.group(1)}')
"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       配置完成！                                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "下一步:"
echo -e "  1. 打开微信开发者工具"
echo -e "  2. 导入项目: ~/Desktop/voiceHealth-miniprogram"
echo -e "  3. 按照 DEPLOY.md 部署云函数"
echo -e "  4. 测试所有功能"
echo -e "  5. 提交审核"
echo ""
echo -e "后端API: ${GREEN}http://localhost:8100${NC}"
echo -e "测试页面: ${GREEN}http://localhost:8100/test${NC}"
echo -e "API文档: ${GREEN}http://localhost:8100/docs${NC}"
