#!/bin/bash
# voice-changer 功能测试脚本

echo "=========================================="
echo "voice-changer 功能测试"
echo "=========================================="

# 设置路径
SKILL_DIR="$HOME/.claude/skills/voice-changer"
SCRIPTS_DIR="$SKILL_DIR/scripts"
CONFIG_DIR="$SKILL_DIR/config"

# 检查依赖
echo ""
echo "1. 检查依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg 未安装"
    echo "   请运行: brew install ffmpeg (macOS)"
    exit 1
fi
echo "✅ FFmpeg: $(ffmpeg -version | head -1)"

# 检查 FFprobe
if ! command -v ffprobe &> /dev/null; then
    echo "❌ FFprobe 未安装"
    exit 1
fi
echo "✅ FFprobe: 已安装"

# 检查脚本文件
echo ""
echo "2. 检查脚本文件..."
if [ -f "$SCRIPTS_DIR/voice_change.py" ]; then
    echo "✅ voice_change.py"
    # 检查语法
    python3 -m py_compile "$SCRIPTS_DIR/voice_change.py" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   语法检查: 通过"
    else
        echo "   ⚠️  语法检查: 失败"
    fi
else
    echo "❌ voice_change.py 不存在"
fi

# 检查配置文件
echo ""
echo "3. 检查配置文件..."
if [ -f "$CONFIG_DIR/voice_config.json" ]; then
    echo "✅ voice_config.json"
    # 验证 JSON 格式
    python3 -c "import json; json.load(open('$CONFIG_DIR/voice_config.json'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   JSON 格式: 有效"
        # 显示声音预设数量
        num_voices=$(python3 -c "import json; print(len(json.load(open('$CONFIG_DIR/voice_config.json'))['voices']))")
        echo "   声音预设数量: $num_voices"
    else
        echo "   ⚠️  JSON 格式: 无效"
    fi
else
    echo "❌ voice_config.json 不存在"
fi

# 显示可用的声音预设
echo ""
echo "4. 可用的声音预设..."
python3 -c "
import json
config = json.load(open('$CONFIG_DIR/voice_config.json'))
for key, voice in config['voices'].items():
    print(f\"  • {key:12} - {voice['name']:15} (音高: {voice['pitch_shift']:+3d})\")
"

# 显示使用方法
echo ""
echo "=========================================="
echo "使用方法："
echo "=========================================="
echo "python3 $SCRIPTS_DIR/voice_change.py <音频文件> [选项]"
echo ""
echo "示例："
echo "  # 基本用法（默认女声）"
echo "  python3 $SCRIPTS_DIR/voice_change.py input.mp3"
echo ""
echo "  # 指定声音类型"
echo "  python3 $SCRIPTS_DIR/voice_change.py input.mp3 -v female_2"
echo ""
echo "  # 自定义音高"
echo "  python3 $SCRIPTS_DIR/voice_change.py input.mp3 -p 7"
echo ""
echo "  # 指定输出文件"
echo "  python3 $SCRIPTS_DIR/voice_change.py input.mp3 -o output.mp3"
echo ""
