#!/usr/bin/env python3
"""
RVC 分批处理长音频
将长音频分割成小段分别处理，然后合并
"""
import os
import sys
import argparse
import numpy as np
import torch
import librosa
import soundfile as sf
from pathlib import Path
import tempfile

# 添加 RVC 路径
SCRIPT_DIR = Path(__file__).parent.parent
RVC_CODE_PATH = SCRIPT_DIR / 'models' / 'Retrieval-based-Voice-Conversion-WebUI'
sys.path.insert(0, str(RVC_CODE_PATH))

def split_audio(audio_path, chunk_duration=60, overlap=2):
    """
    分割音频为小段

    Args:
        audio_path: 输入音频文件
        chunk_duration: 每段时长（秒）
        overlap: 重叠时长（秒）

    Returns:
        list of (audio_segment, start_time, end_time)
    """
    audio, sr = librosa.load(audio_path, sr=None)
    duration = len(audio) / sr

    chunk_samples = int(chunk_duration * sr)
    overlap_samples = int(overlap * sr)

    segments = []
    start = 0

    while start < len(audio):
        end = min(start + chunk_samples, len(audio))

        segment_audio = audio[start:end]
        start_time = start / sr
        end_time = end / sr

        segments.append((segment_audio, sr, start_time, end_time))

        start += (chunk_samples - overlap_samples)

    return segments

def merge_audio_segments(segment_paths, output_path, sample_rate, overlap_seconds=2):
    """合并音频段，去掉重叠部分"""
    import subprocess

    all_audio = []
    overlap_samples = int(overlap_seconds * sample_rate)

    for i, seg_path in enumerate(segment_paths):
        audio, sr = librosa.load(seg_path, sr=sample_rate)

        if i == 0:
            # 第一段：全部保留
            all_audio.append(audio)
        elif i == len(segment_paths) - 1:
            # 最后一段：去掉重叠部分
            all_audio.append(audio[overlap_samples:])
        else:
            # 中间段：去掉重叠部分
            all_audio.append(audio[overlap_samples:])

    # 连接所有段
    merged_audio = np.concatenate(all_audio, axis=0)

    # 先保存为临时 WAV 文件
    temp_wav = output_path.rsplit('.', 1)[0] + '_temp.wav'
    sf.write(temp_wav, merged_audio, sample_rate)
    print(f"  已合并 {len(segment_paths)} 个音频段（已去除 {overlap_seconds} 秒重叠）")

    # 如果输出是 MP3，使用 ffmpeg 转换（40000Hz 需要重采样）
    if output_path.lower().endswith('.mp3'):
        print(f"  正在转换为 MP3...")
        cmd = [
            'ffmpeg', '-y',
            '-i', temp_wav,
            '-ar', '48000',  # 重采样到 48000 Hz（MP3 兼容）
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            os.unlink(temp_wav)
            print(f"  MP3 转换完成")
        else:
            print(f"  ⚠️  MP3 转换失败，保留 WAV 文件: {temp_wav}")
            if result.stderr:
                print(f"  错误: {result.stderr}")
            # 如果转换失败，保留 WAV 文件并返回 False
            return False
    else:
        # 非 MP3 格式，直接重命名
        import shutil
        shutil.move(temp_wav, output_path)

    return True

def get_rvc_python():
    """获取 RVC Python 解释器路径（优先使用 Python 3.10）"""
    rvc_env_310 = SCRIPT_DIR / 'models' / 'rvc_env_310' / 'bin' / 'python3'
    rvc_env = SCRIPT_DIR / 'models' / 'rvc_env' / 'bin' / 'python3'

    if rvc_env_310.exists():
        return str(rvc_env_310)
    elif rvc_env.exists():
        return str(rvc_env)
    else:
        return 'python3'

def process_audio_segment(segment_audio, sr, model_path, f0up_key, device="cpu"):
    """处理单个音频段"""
    import subprocess

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
        sf.write(temp_input.name, segment_audio, sr)
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
        temp_output_path = temp_output.name

    try:
        # 使用 RVC 推理脚本
        rvc_script = SCRIPT_DIR / 'scripts' / 'rvc_infer_real.py'
        python_exe = get_rvc_python()

        cmd = [
            python_exe,
            str(rvc_script),
            temp_input_path,
            '-o', temp_output_path,
            '-m', model_path,
            '-p', str(f0up_key),
            '-f', 'harvest',
            '-d', device
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and os.path.exists(temp_output_path):
            audio, sr = librosa.load(temp_output_path, sr=None)
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
            return audio, sr
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            raise RuntimeError(f"RVC 推理失败: {error_msg}")

    finally:
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)

def process_long_audio(input_audio, output_audio, model_path, f0up_key=0, device="cpu"):
    """处理长音频"""
    print(f"正在处理长音频，将分批处理...")

    segments = split_audio(input_audio, chunk_duration=30, overlap=2)

    print(f"  分成 {len(segments)} 段")

    processed_segments = []
    temp_dir = tempfile.mkdtemp()

    try:
        for i, (segment_audio, sr, start_time, end_time) in enumerate(segments):
            print(f"  处理第 {i+1}/{len(segments)} 段 ({start_time:.1f}s - {end_time:.1f}s)...")

            try:
                # 处理这一段
                processed_audio, out_sr = process_audio_segment(
                    segment_audio, sr, model_path, f0up_key, device
                )

                # 保存到临时文件
                seg_path = os.path.join(temp_dir, f"segment_{i:04d}.wav")
                sf.write(seg_path, processed_audio, out_sr)
                processed_segments.append(seg_path)

                print(f"    完成")

            except Exception as e:
                # 不降级：RVC 失败则整个处理失败
                print(f"    ❌ 第 {i+1} 段 RVC 处理失败，不降级")
                print(f"    错误: {e}")
                # 清理临时文件
                for seg_path in processed_segments:
                    if os.path.exists(seg_path):
                        os.unlink(seg_path)
                os.rmdir(temp_dir)
                raise RuntimeError(f"RVC 处理失败（第 {i+1} 段）: {e}")

        # 合并所有段
        print(f"  正在合并音频段...")
        merge_success = merge_audio_segments(processed_segments, output_audio, 40000, overlap_seconds=2)

        # 清理临时文件
        for seg_path in processed_segments:
            os.unlink(seg_path)
        os.rmdir(temp_dir)

        return merge_success

    except Exception as e:
        print(f"  处理失败: {e}")
        # 清理
        if os.path.exists(temp_dir):
            for seg_path in processed_segments:
                if os.path.exists(seg_path):
                    os.unlink(seg_path)
            os.rmdir(temp_dir)
        return False

def main():
    parser = argparse.ArgumentParser(description='RVC 长音频处理')
    parser.add_argument('input', help='输入音频文件')
    parser.add_argument('-o', '--output', required=True, help='输出音频文件')
    parser.add_argument('-m', '--model', required=True, help='RVC 模型路径')
    parser.add_argument('-p', '--pitch', type=int, default=0, help='音高调整（半音）')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"输入文件不存在: {args.input}")
        sys.exit(1)

    model_path = os.path.expanduser(args.model)
    if not os.path.exists(model_path):
        print(f"模型文件不存在: {model_path}")
        sys.exit(1)

    print("使用 CPU 处理...")
    success = process_long_audio(args.input, args.output, model_path, args.pitch, "cpu")

    if success:
        print(f"✅ 处理完成！")
        print(f"输出文件: {args.output}")
        sys.exit(0)
    else:
        print("❌ 处理失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
