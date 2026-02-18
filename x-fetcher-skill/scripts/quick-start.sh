#!/bin/bash
# X Fetcher Skill 快速开始脚本

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "======================================"
echo "  X Fetcher Skill - 快速开始"
echo "======================================"
echo ""

# 检查 Python
echo "🔍 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    echo "请先安装 Python 3.6 或更高版本"
    exit 1
fi
echo "✅ Python 已安装: $(python3 --version)"

# 检查依赖
echo ""
echo "🔍 检查依赖..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  requests 未安装"
    echo "正在安装依赖..."
    pip3 install -q -r "$SKILL_DIR/scripts/requirements.txt"
fi
echo "✅ 依赖已安装"

# 检查配置文件
echo ""
echo "🔍 检查配置文件..."
CONFIG_FOUND=false

if [ -f "$HOME/.x-fetcher/EXTEND.md" ]; then
    echo "✅ 找到用户级配置: ~/.x-fetcher/EXTEND.md"
    CONFIG_FOUND=true
elif [ -f ".x-fetcher/EXTEND.md" ]; then
    echo "✅ 找到项目级配置: .x-fetcher/EXTEND.md"
    CONFIG_FOUND=true
fi

if [ "$CONFIG_FOUND" = false ]; then
    echo "⚠️  未找到配置文件"
    echo ""
    echo "正在创建默认配置..."
    mkdir -p "$HOME/.x-fetcher"

    cat > "$HOME/.x-fetcher/EXTEND.md" << 'EOF'
---
default_output_dir: ~/x-fetcher
auto_save: true
download_media: ask
---
EOF

    echo "✅ 配置文件已创建: ~/.x-fetcher/EXTEND.md"
    echo "   默认保存目录: ~/x-fetcher"
    echo ""
    echo "💡 你可以编辑配置文件来修改设置:"
    echo "   nano ~/.x-fetcher/EXTEND.md"
fi

# 测试运行
echo ""
echo "======================================"
echo "  准备就绪！"
echo "======================================"
echo ""
echo "使用示例:"
echo ""
echo "1. 抓取推文:"
echo "   python3 scripts/main.py \"https://x.com/username/status/123\""
echo ""
echo "2. 检查配置:"
echo "   python3 scripts/main.py --check-config"
echo ""
echo "3. 只输出 JSON:"
echo "   python3 scripts/main.py \"https://x.com/username/status/123\" --json"
echo ""
echo "详细使用说明:"
echo "  cat $SKILL_DIR/USAGE.md"
echo ""
