#!/bin/bash
# voice-changer 依赖安装脚本

echo "=========================================="
echo "voice-changer 依赖安装"
echo "=========================================="

# 检查操作系统
OS="$(uname -s)"
echo "检测到操作系统: $OS"
echo ""

# 1. 检查并安装 FFmpeg
echo "1. 检查 FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg 已安装: $(ffmpeg -version | head -1)"
else
    echo "❌ FFmpeg 未安装"
    echo "正在安装 FFmpeg..."

    case "$OS" in
        Darwin)
            # macOS
            if command -v brew &> /dev/null; then
                brew install ffmpeg
            else
                echo "❌ 请先安装 Homebrew: https://brew.sh"
                exit 1
            fi
            ;;
        Linux)
            # Linux
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y ffmpeg
            elif command -v yum &> /dev/null; then
                sudo yum install -y ffmpeg
            else
                echo "❌ 不支持的 Linux 发行版，请手动安装 FFmpeg"
                exit 1
            fi
            ;;
        *)
            echo "❌ 不支持的操作系统"
            exit 1
            ;;
    esac

    # 验证安装
    if command -v ffmpeg &> /dev/null; then
        echo "✅ FFmpeg 安装成功"
    else
        echo "❌ FFmpeg 安装失败"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ 所有依赖安装完成！"
echo "=========================================="
echo ""
echo "voice-changer 使用 simple 方法（FFmpeg 音高调整）"
echo "无需额外的 Python 依赖"
echo ""
echo "如需使用 RVC 方法（AI 模型），请手动安装："
echo "  pip install torch librosa soundfile"
echo ""
