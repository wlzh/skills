#!/usr/bin/env python3
"""
音频转录脚本 - 使用 FunASR 进行 30s 分段转录
获取字符级时间戳，用于后续关键字定位和剪辑
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def get_audio_duration(audio_file):
    """获取音频时长（秒）"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_audio_segment(audio_file, start, duration, output_wav):
    """提取音频片段并转换为 16kHz 单声道 WAV"""
    cmd = [
        'ffmpeg', '-y', '-i', audio_file,
        '-ss', str(start),
        '-t', str(duration),
        '-vn',  # 不要视频
        '-acodec', 'pcm_s16le',  # 16-bit PCM
        '-ar', '16000',  # 16kHz 采样率
        '-ac', '1',  # 单声道
        output_wav
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def transcribe_with_funasr(audio_file, output_json, segment_length=30):
    """
    使用 FunASR 进行 30s 分段转录

    Args:
        audio_file: 输入音频文件路径
        output_json: 输出 JSON 文件路径
        segment_length: 分段长度（秒），默认 30

    Returns:
        转录结果字典
    """
    print(f"🎤 开始转录音频: {audio_file}")

    # 检查 FunASR 是否安装
    try:
        from funasr import AutoModel
    except ImportError:
        print("❌ 错误: FunASR 未安装")
        print("请运行: pip install funasr modelscope")
        sys.exit(1)

    # 获取音频时长
    duration = get_audio_duration(audio_file)
    print(f"📊 音频时长: {duration:.2f}秒")

    # 加载 FunASR 模型
    print("🔧 加载 FunASR 模型...")
    model = AutoModel(
        model="paraformer-zh",
        disable_update=True
    )

    # 分段转录
    all_chars = []
    num_segments = int(duration // segment_length) + 1

    print(f"📝 开始分段转录（共 {num_segments} 段）...")

    for i in range(num_segments):
        start = i * segment_length
        dur = min(segment_length, duration - start)

        if dur <= 0:
            break

        # 提取音频段
        wav_file = f'/tmp/audiocut_seg_{i}.wav'
        extract_audio_segment(audio_file, start, dur, wav_file)

        # FunASR 转录（字符级时间戳）
        result = model.generate(
            input=wav_file,
            return_raw_text=True,
            timestamp_granularity="character"
        )

        # 处理转录结果
        for item in result:
            if 'timestamp' in item and 'text' in item:
                text = item['text'].replace(' ', '')

                # 确保时间戳数量匹配
                timestamps = item['timestamp']
                for idx, char in enumerate(text):
                    if idx < len(timestamps):
                        ts = timestamps[idx]
                        all_chars.append({
                            'char': char,
                            'start': round(start + ts[0] / 1000, 2),
                            'end': round(start + ts[1] / 1000, 2)
                        })

        # 清理临时文件
        os.remove(wav_file)

        # 显示进度
        progress = (i + 1) / num_segments * 100
        print(f"   进度: {progress:.1f}% ({i+1}/{num_segments})")

    # 构建完整文本
    full_text = ''.join([c['char'] for c in all_chars])

    # 保存结果
    result_data = {
        'audio_file': str(audio_file),
        'duration': duration,
        'total_chars': len(all_chars),
        'full_text': full_text,
        'chars': all_chars
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 转录完成！")
    print(f"   总字符数: {len(all_chars)}")
    print(f"   输出文件: {output_json}")

    return result_data

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python transcribe_audio.py <音频文件> [输出JSON]")
        sys.exit(1)

    audio_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else audio_file.replace('.mp3', '_transcript.json')

    transcribe_with_funasr(audio_file, output_json)
