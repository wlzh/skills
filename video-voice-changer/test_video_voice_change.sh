#!/bin/bash
# video-voice-changer 测试脚本

echo "=================================="
echo "video-voice-changer 环境检测"
echo "=================================="
echo ""

PASS=0
FAIL=0

# 检查 Python3
echo -n "检查 Python3... "
if command -v python3 &> /dev/null; then
    echo "✅ 已安装 ($(python3 --version))"
    ((PASS++))
else
    echo "❌ 未安装"
    ((FAIL++))
fi

# 检查 FFmpeg
echo -n "检查 FFmpeg... "
if command -v ffmpeg &> /dev/null; then
    echo "✅ 已 installed"
    ((PASS++))
else
    echo "❌ 未安装"
    ((FAIL++))
fi

# 检查 FFprobe
echo -n "检查 FFprobe... "
if command -v ffprobe &> /dev/null; then
    echo "✅ 已安装"
    ((PASS++))
else
    echo "❌ 未安装"
    ((FAIL++))
fi

# 检查脚本存在
echo -n "检查 video_voice_change.py... "
SCRIPT_PATH="$HOME/.claude/skills/video-voice-changer/scripts/video_voice_change.py"
if [ -f "$SCRIPT_PATH" ]; then
    echo "✅ 存在"
    ((PASS++))
else
    echo "❌ 不存在"
    ((FAIL++))
fi

# 检查脚本语法
echo -n "检查脚本语法... "
if python3 -m py_compile "$SCRIPT_PATH" 2>/dev/null; then
    echo "✅ 语法正确"
    ((PASS++))
else
    echo "❌ 语法错误"
    ((FAIL++))
fi

# 检查 voice-changer skill
echo -n "检查 voice-changer skill... "
VOICE_CHANGER="$HOME/.claude/skills/voice-changer/scripts/voice_change.py"
if [ -f "$VOICE_CHANGER" ]; then
    echo "✅ 存在"
    ((PASS++))
else
    echo "❌ 不存在（video-voice-changer 需要 voice-changer）"
    ((FAIL++))
fi

# 检查配置文件
echo -n "检查 voice-changer 配置... "
CONFIG_PATH="$HOME/.claude/skills/voice-changer/config/voice_config.json"
if [ -f "$CONFIG_PATH" ]; then
    echo "✅ 存在"
    ((PASS++))
else
    echo "❌ 不存在"
    ((FAIL++))
fi

echo ""
echo "=================================="
echo "检测结果: $PASS 通过, $FAIL 失败"
echo "=================================="

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "✅ 所有检查通过！"
    echo ""
    echo "使用方法:"
    echo "  python3 $SCRIPT_PATH <视频文件>"
    echo ""
    echo "示例:"
    echo "  python3 $SCRIPT_PATH video.mp4"
    echo "  python3 $SCRIPT_PATH video.mp4 -v male_deep -o output.mp4"
    exit 0
else
    echo ""
    echo "❌ 部分检查失败，请安装缺失的依赖"
    echo ""
    echo "安装 FFmpeg (macOS):"
    echo "  brew install ffmpeg"
    echo ""
    echo "安装 FFmpeg (Ubuntu/Debian):"
    echo "  sudo apt-get install ffmpeg"
    exit 1
fi
