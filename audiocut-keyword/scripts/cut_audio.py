#!/usr/bin/env python3
"""
音频剪辑脚本 - 使用 FFmpeg 删除指定时间段
"""

import subprocess
import sys
import json
from pathlib import Path

def generate_ffmpeg_filter(delete_segments, total_duration):
    """
    生成 FFmpeg filter_complex 命令

    Args:
        delete_segments: 要删除的时间段列表 [(start, end), ...]
        total_duration: 音频总时长

    Returns:
        filter_complex 字符串
    """
    # 计算保留的片段
    keep_segments = []
    last_end = 0.0

    for start, end in sorted(delete_segments):
        if start > last_end:
            keep_segments.append((last_end, start))
        last_end = max(last_end, end)

    # 添加最后一段
    if last_end < total_duration:
        keep_segments.append((last_end, total_duration))

    if not keep_segments:
        print("⚠️  警告: 没有保留的片段")
        return None

    # 生成 filter_complex
    filter_lines = []

    for i, (start, end) in enumerate(keep_segments):
        filter_lines.append(
            f"[0:a]atrim=start={start:.2f}:end={end:.2f},"
            f"asetpts=PTS-STARTPTS[a{i}];"
        )

    # 拼接所有片段
    concat_inputs = ''.join([f"[a{i}]" for i in range(len(keep_segments))])
    concat_line = f"{concat_inputs}concat=n={len(keep_segments)}:v=0:a=1[outa]"

    filter_complex = ''.join(filter_lines) + concat_line

    return filter_complex, keep_segments

def cut_audio(input_audio, output_audio, delete_segments, total_duration):
    """
    执行音频剪辑

    Args:
        input_audio: 输入音频文件
        output_audio: 输出音频文件
        delete_segments: 要删除的时间段
        total_duration: 音频总时长
    """
    print(f"✂️  开始剪辑音频...")
    print(f"   输入: {input_audio}")
    print(f"   输出: {output_audio}")
    print(f"   删除片段数: {len(delete_segments)}")

    # 生成 filter
    result = generate_ffmpeg_filter(delete_segments, total_duration)
    if not result:
        print("❌ 无法生成剪辑计划")
        return False

    filter_complex, keep_segments = result

    # 计算删除和保留的时长
    delete_duration = sum(end - start for start, end in delete_segments)
    keep_duration = sum(end - start for start, end in keep_segments)

    print(f"   原始时长: {total_duration:.2f}s")
    print(f"   删除时长: {delete_duration:.2f}s ({delete_duration/total_duration*100:.1f}%)")
    print(f"   保留时长: {keep_duration:.2f}s ({keep_duration/total_duration*100:.1f}%)")

    # 执行 FFmpeg 命令
    cmd = [
        'ffmpeg', '-y', '-i', input_audio,
        '-filter_complex', filter_complex,
        '-map', '[outa]',
        output_audio
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 剪辑完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg 执行失败:")
        print(e.stderr.decode())
        return False

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("用法: python cut_audio.py <输入音频> <输出音频> <删除计划JSON>")
        sys.exit(1)

    input_audio = sys.argv[1]
    output_audio = sys.argv[2]
    delete_plan_file = sys.argv[3]

    # 加载删除计划
    with open(delete_plan_file, 'r') as f:
        data = json.load(f)

    delete_segments = data['delete_segments']
    total_duration = data['total_duration']

    cut_audio(input_audio, output_audio, delete_segments, total_duration)
