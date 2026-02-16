#!/usr/bin/env python3
"""
video_voice_change.py - 视频变声处理脚本

对视频文件中的音频进行变声处理，然后将处理后的音频与视频重新合并
使用 voice-changer skill 进行音频变声
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path

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
        print(f"缺少依赖: {', '.join(missing)}")
        return False

    return True

def get_video_duration(video_file):
    """获取视频时长"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_video_info(video_file):
    """获取视频信息"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height',
        '-of', 'json',
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        import json
        return json.loads(result.stdout)
    return None

def extract_audio(video_file, audio_file):
    """从视频中提取音频"""
    print(f"正在从视频中提取音频...")
    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-vn',
        '-acodec', 'libmp3lame',
        '-q:a', '2',
        '-y',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"音频提取失败: {result.stderr}")
        return False
    print(f"音频已提取: {audio_file}")
    return True

def change_audio_voice(input_audio, output_audio, voice_type, config_path=None):
    """调用 voice-changer skill 进行变声"""
    print(f"正在调用 voice-changer skill 进行变声...")
    print(f"目标声音: {voice_type}")

    # 获取 voice-changer 脚本路径
    script_dir = Path(__file__).parent.parent.parent
    voice_changer_script = script_dir / 'voice-changer' / 'scripts' / 'voice_change.py'

    if not voice_changer_script.exists():
        print(f"错误: voice-changer skill 不存在: {voice_changer_script}")
        return False

    cmd = [
        'python3',
        str(voice_changer_script),
        input_audio,
        '-v', voice_type,
        '-o', output_audio
    ]

    if config_path:
        cmd.extend(['-c', config_path])

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 打印 voice-changer 的输出
    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        print(f"变声失败: {result.stderr}")
        return False

    return True

def merge_audio_video(video_file, audio_file, output_file):
    """将变声后的音频与视频合并"""
    print(f"正在合并音频和视频...")

    # 使用 ffmpeg 合并，保持视频编码，替换音频
    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',  # 复制视频流，不重新编码
        '-c:a', 'aac',    # 音频编码为 AAC
        '-map', '0:v:0',  # 使用输入文件的视频
        '-map', '1:a:0',  # 使用新音频
        '-shortest',      # 以最短的流为准
        '-y',
        output_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"合并失败: {result.stderr}")
        return False
    print(f"合并完成: {output_file}")
    return True

def load_voice_config(config_path=None):
    """加载 voice-changer 的配置文件"""
    if config_path:
        config_file = Path(config_path)
    else:
        script_dir = Path(__file__).parent.parent.parent
        config_file = script_dir / 'voice-changer' / 'config' / 'voice_config.json'

    if not config_file.exists():
        return {
            'voices': {
                'female_1': {'pitch_shift': 1},
                'female_2': {'pitch_shift': 7},
                'female_3': {'pitch_shift': 4},
                'male_deep': {'pitch_shift': -5},
                'male_normal': {'pitch_shift': -3},
                'child': {'pitch_shift': 8},
                'robot': {'pitch_shift': 0}
            },
            'default_voice': 'female_1'
        }

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='视频变声处理工具 - 对视频中的音频进行变声')
    parser.add_argument('input_video', help='输入视频文件路径')
    parser.add_argument('-v', '--voice', default='female_1',
                       help='目标声音类型（默认: female_1）')
    parser.add_argument('-o', '--output', help='输出视频文件路径（默认: 原文件名_vc.后缀）')
    parser.add_argument('--overwrite', action='store_true',
                       help='覆盖原视频文件（默认: 创建新文件）')
    parser.add_argument('-c', '--config', help='voice-changer 配置文件路径')
    parser.add_argument('--keep-audio', action='store_true',
                       help='保留提取的原始音频文件')
    parser.add_argument('--temp-dir', help='自定义临时目录')

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input_video):
        print(f"输入文件不存在: {args.input_video}")
        sys.exit(1)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 确定输出文件路径
    input_path = Path(args.input_video)

    if args.output:
        output_video = args.output
    elif args.overwrite:
        # 使用 --overwrite 参数时才覆盖原视频
        output_video = args.input_video
    else:
        # 默认创建新文件，添加 _vc 后缀
        output_video = str(input_path.parent / f"{input_path.stem}_vc{input_path.suffix}")

    print("=" * 50)
    print("视频变声处理")
    print("=" * 50)
    print(f"输入文件: {args.input_video}")
    print(f"输出文件: {output_video}")
    print(f"目标声音: {args.voice}")
    print()

    # 获取视频信息
    try:
        duration = get_video_duration(args.input_video)
        print(f"视频时长: {duration:.2f} 秒 ({duration/60:.1f} 分钟)")
    except Exception as e:
        print(f"无法获取视频时长: {e}")
        duration = 0

    video_info = get_video_info(args.input_video)
    if video_info and video_info.get('streams'):
        stream = video_info['streams'][0]
        print(f"视频编码: {stream.get('codec_name', 'N/A')}")
        print(f"分辨率: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}")
    print()

    # 创建临时目录
    if args.temp_dir:
        temp_dir = Path(args.temp_dir)
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix='video_voice_change_'))

    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 步骤 1: 从视频中提取音频
        temp_audio = temp_dir / f"{input_path.stem}_original.mp3"
        if not extract_audio(args.input_video, str(temp_audio)):
            sys.exit(1)

        # 步骤 2: 对音频进行变声
        changed_audio = temp_dir / f"{input_path.stem}_changed.mp3"
        if not change_audio_voice(str(temp_audio), str(changed_audio), args.voice, args.config):
            sys.exit(1)

        # 步骤 3: 将变声后的音频与视频合并
        if output_video == args.input_video:
            # 如果输出是原文件，先输出到临时文件再移动
            temp_output = temp_dir / f"{input_path.stem}_output{input_path.suffix}"
            if not merge_audio_video(args.input_video, str(changed_audio), str(temp_output)):
                sys.exit(1)
            # 移动临时文件到目标位置
            shutil.move(str(temp_output), output_video)
        else:
            if not merge_audio_video(args.input_video, str(changed_audio), output_video):
                sys.exit(1)

        print()
        print("=" * 50)
        print("变声处理完成!")
        print(f"输出文件: {output_video}")

        # 显示文件大小
        output_size = os.path.getsize(output_video) / (1024 * 1024)
        print(f"文件大小: {output_size:.2f} MB")
        print("=" * 50)

        # 如果用户要求保留音频，复制到输出位置
        if args.keep_audio:
            audio_output = input_path.parent / f"{input_path.stem}_voice_changed.mp3"
            shutil.copy2(changed_audio, audio_output)
            print(f"原始音频已保存: {audio_output}")

    finally:
        # 清理临时文件
        if not args.keep_audio and temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()
