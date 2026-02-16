#!/bin/bash
# audiocut-keyword 功能测试脚本

echo "=========================================="
echo "audiocut-keyword 功能测试"
echo "=========================================="

# 设置路径
SKILL_DIR="$HOME/.claude/skills/audiocut-keyword"
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
    exit 1
fi
echo "✅ FFmpeg: $(ffmpeg -version | head -1)"

# 检查 FunASR
echo ""
echo "2. 检查 FunASR..."
python3 -c "import funasr" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ FunASR 已安装"
else
    echo "⚠️  FunASR 未安装，需要运行: pip install funasr modelscope"
fi

# 检查脚本文件
echo ""
echo "3. 检查脚本文件..."
for script in transcribe_audio.py detect_keywords.py cut_audio.py audiocut_keyword.py; do
    if [ -f "$SCRIPTS_DIR/$script" ]; then
        echo "✅ $script"
    else
        echo "❌ $script 不存在"
    fi
done

# 检查配置文件
echo ""
echo "4. 检查配置文件..."
if [ -f "$CONFIG_DIR/keywords.json" ]; then
    echo "✅ keywords.json"
    echo "   关键字数量: $(python3 -c "import json; print(len(json.load(open('$CONFIG_DIR/keywords.json'))['keywords']))")"
else
    echo "❌ keywords.json 不存在"
fi

# 显示使用方法
echo ""
echo "=========================================="
echo "使用方法："
echo "=========================================="
echo "python3 $SCRIPTS_DIR/audiocut_keyword.py <音频文件>"
echo ""
echo "示例："
echo "python3 $SCRIPTS_DIR/audiocut_keyword.py input.mp3"
echo ""
