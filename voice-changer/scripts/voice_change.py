#!/usr/bin/env python3
"""
voice_change.py - 音频变声处理脚本

使用 RVC (Retrieval-based Voice Conversion) 进行音频变声
支持多种预设声音模型，可将音频转换为不同的声音
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

def get_audio_duration(audio_file):
    """获取音频时长"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_audio_sample_rate(audio_file):
    """获取音频采样率"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=sample_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(result.stdout.strip())

def check_dependencies():
    """检查必要的依赖"""
    dependencies = {
        'ffmpeg': 'FFmpeg',
        'ffprobe': 'FFprobe',
        'python3': 'Python3'
    }

    missing = []
    for cmd, name in dependencies.items():
        if subprocess.run(['which', cmd], capture_output=True).returncode != 0:
            missing.append(name)

    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        return False

    return True

def load_config(config_path=None):
    """加载配置文件"""
    if config_path is None:
        script_dir = Path(__file__).parent.parent
        config_path = script_dir / 'config' / 'voice_config.json'

    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def change_voice_simple(input_audio, output_audio, pitch_shift=5):
    """
    使用 FFmpeg 进行简单变声（音高调整）
    这是一个轻量级方案，不需要额外的 AI 模型

    pitch_shift: 音高调整（半音）
        正值：音调升高（女声效果）
        负值：音调降低（男声效果）
        建议范围: -12 到 +12
    """
    print(f"🎵 使用 FFmpeg 进行音高调整...")
    print(f"   音高偏移: {pitch_shift:+d} 半音")

    # 如果 pitch_shift 为 0，直接复制文件
    if pitch_shift == 0:
        print(f"   音高偏移为 0，直接复制文件（保持原样）")
        import shutil
        shutil.copy2(input_audio, output_audio)
        return True

    # 获取输入文件的采样率
    try:
        sample_rate = get_audio_sample_rate(input_audio)
        print(f"   输入采样率: {sample_rate} Hz")
    except Exception as e:
        print(f"⚠️  无法获取采样率，使用默认值 44100 Hz: {e}")
        sample_rate = 44100

    # 计算音高调整比率
    # 每个半音对应 2^(1/12) 的频率比
    pitch_ratio = 2 ** (pitch_shift / 12.0)

    # 使用 asetrate + aresample + atempo 组合进行音高调整（保持时长）
    # 关键：使用实际的采样率，而不是硬编码 44100
    cmd = [
        'ffmpeg',
        '-i', input_audio,
        '-af', f'asetrate={sample_rate}*{pitch_ratio},aresample={sample_rate},atempo={1/pitch_ratio}',
        '-y',
        output_audio
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"❌ FFmpeg 处理失败: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("❌ 处理超时")
        return False
    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return False

def change_voice_rvc(input_audio, output_audio, voice_config):
    """
    使用 RVC 模型进行高质量变声
    需要预先安装 RVC 相关依赖和模型
    """
    print(f"🎤 使用 RVC 模型进行变声...")
    print(f"   模型: {voice_config.get('model_path', 'N/A')}")

    # 检查是否安装了 RVC
    try:
        import torch
        import librosa
        import soundfile as sf
    except ImportError as e:
        print(f"❌ 缺少 RVC 依赖: {e}")
        print("   请运行: pip install torch librosa soundfile")
        return False

    # TODO: 实现 RVC 变声逻辑
    # 这里需要集成实际的 RVC 模型推理代码
    print("⚠️  RVC 模型集成待实现，当前使用简单音高调整")

    # 暂时使用简单方案
    pitch_shift = voice_config.get('pitch_shift', 5)
    return change_voice_simple(input_audio, output_audio, pitch_shift)

def main():
    parser = argparse.ArgumentParser(description='音频变声处理工具')
    parser.add_argument('input_audio', help='输入音频文件路径')
    parser.add_argument('-o', '--output', help='输出音频文件路径（默认: 输入文件名_voice_changed.mp3）')
    parser.add_argument('-v', '--voice', default='female_1', help='目标声音类型（默认: female_1）')
    parser.add_argument('-c', '--config', help='自定义配置文件路径')
    parser.add_argument('-m', '--method', choices=['simple', 'rvc'], default='simple',
                       help='变声方法: simple(快速音高调整) 或 rvc(AI模型，需额外安装)')
    parser.add_argument('-p', '--pitch', type=int, help='音高调整（半音，覆盖配置文件）')

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input_audio):
        print(f"❌ 输入文件不存在: {args.input_audio}")
        sys.exit(1)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 确定输出文件路径
    if args.output:
        output_audio = args.output
    else:
        input_path = Path(args.input_audio)
        output_audio = str(input_path.parent / f"{input_path.stem}_voice_changed{input_path.suffix}")

    print("=" * 50)
    print("🎙️  音频变声处理")
    print("=" * 50)
    print(f"输入文件: {args.input_audio}")
    print(f"输出文件: {output_audio}")
    print(f"目标声音: {args.voice}")
    print(f"处理方法: {args.method}")

    # 获取音频时长
    try:
        duration = get_audio_duration(args.input_audio)
        print(f"音频时长: {duration:.2f} 秒")
    except Exception as e:
        print(f"⚠️  无法获取音频时长: {e}")

    print()

    # 加载配置
    config = load_config(args.config)

    # 获取声音配置
    if args.voice not in config.get('voices', {}):
        print(f"⚠️  未找到声音配置 '{args.voice}'，使用默认配置")
        voice_config = {
            'pitch_shift': 5 if 'female' in args.voice else -5
        }
    else:
        voice_config = config['voices'][args.voice]

    # 如果命令行指定了音高，覆盖配置
    if args.pitch is not None:
        voice_config['pitch_shift'] = args.pitch
        print(f"使用命令行指定的音高: {args.pitch:+d} 半音")

    # 执行变声
    success = False
    if args.method == 'simple':
        pitch_shift = voice_config.get('pitch_shift', 5)
        success = change_voice_simple(args.input_audio, output_audio, pitch_shift)
    elif args.method == 'rvc':
        success = change_voice_rvc(args.input_audio, output_audio, voice_config)

    if success:
        print()
        print("=" * 50)
        print("✅ 变声处理完成！")
        print(f"输出文件: {output_audio}")

        # 显示文件大小
        output_size = os.path.getsize(output_audio) / (1024 * 1024)
        print(f"文件大小: {output_size:.2f} MB")
        print("=" * 50)
    else:
        print()
        print("❌ 变声处理失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
