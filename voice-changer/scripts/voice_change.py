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

def change_voice_pedalboard(input_audio, output_audio, pitch_shift=5, voice_type="female"):
    """
    使用 pedalboard 进行高质量音高调整和音色变换
    pedalboard 是 Spotify 开发的专业音频处理库

    pitch_shift: 音高调整（半音）
        正值：音调升高（女声效果）
        负值：音调降低（男声效果）
        建议范围: -12 到 +12
    voice_type: 声音类型，影响额外的音频处理效果
    """
    print(f"🎛️ 使用 Pedalboard 进行音高和音色调整...")
    print(f"   音高偏移: {pitch_shift:+d} 半音")
    print(f"   声音类型: {voice_type}")

    # 如果 pitch_shift 为 0，直接复制文件
    if pitch_shift == 0:
        print(f"   音高偏移为 0，直接复制文件（保持原样）")
        import shutil
        shutil.copy2(input_audio, output_audio)
        return True

    # 检查是否安装了 pedalboard
    try:
        from pedalboard import Pedalboard, PitchShift, Reverb, Chorus, Phaser, Distortion, Compressor, HighpassFilter, LowpassFilter, Gain
        from pedalboard.io import AudioFile
    except ImportError:
        print("❌ 未安装 pedalboard")
        print("   请运行: pip install pedalboard")
        return False

    try:
        # 根据声音类型创建不同的效果链
        effects = [PitchShift(semitones=pitch_shift)]

        # 添加额外的效果使声音更自然
        if "female" in voice_type:
            # 女声效果：添加轻微的混响和高通滤波
            effects.extend([
                HighpassFilter(cutoff_frequency_hz=150),  # 去除低频
                Compressor(threshold_db=-20, ratio=2.5),  # 压缩动态范围
                Gain(gain_db=2),  # 轻微提升音量
            ])
        elif "male" in voice_type:
            # 男声效果：添加低通滤波
            effects.extend([
                LowpassFilter(cutoff_frequency_hz=4000),  # 去除高频
                Compressor(threshold_db=-15, ratio=2),
                Gain(gain_db=3),
            ])
        elif "child" in voice_type:
            # 童声效果：更明亮
            effects.extend([
                HighpassFilter(cutoff_frequency_hz=200),
                Compressor(threshold_db=-25, ratio=3),
                Gain(gain_db=4),
            ])

        # 创建效果链
        board = Pedalboard(effects)

        # 读取输入音频
        with AudioFile(input_audio) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        print(f"   输入采样率: {samplerate} Hz")
        print(f"   音频形状: {audio.shape}")
        print(f"   效果链: {len(effects)} 个效果")

        # 处理音频
        print(f"   正在处理...")
        effected = board(audio, samplerate)

        # 保存输出音频
        with AudioFile(output_audio, 'w', samplerate, effected.shape[0]) as f:
            f.write(effected)

        return True

    except Exception as e:
        print(f"❌ Pedalboard 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def change_voice_pedalboard_enhanced(input_audio, output_audio, pitch_shift=5, voice_type="rvc"):
    """
    增强版 Pedalboard 变声 - 更多效果处理，用于 RVC 后备方案
    """
    print(f"🎛️ 使用增强版 Pedalboard 进行音高和音色调整...")
    print(f"   音高偏移: {pitch_shift:+d} 半音")
    print(f"   声音类型: {voice_type}")

    if pitch_shift == 0:
        print(f"   音高偏移为 0，直接复制文件（保持原样）")
        import shutil
        shutil.copy2(input_audio, output_audio)
        return True

    try:
        from pedalboard import Pedalboard, PitchShift, Reverb, Chorus, Phaser, Distortion, Compressor, HighpassFilter, LowpassFilter, Gain, Limiter, Delay
        from pedalboard.io import AudioFile

        # 根据声音类型创建增强效果链
        effects = [PitchShift(semitones=pitch_shift)]

        if "female" in voice_type:
            # 女声增强效果
            effects.extend([
                HighpassFilter(cutoff_frequency_hz=200),
                Compressor(threshold_db=-18, ratio=3),
                Chorus(rate_hz=1.5, depth=0.3, wet_level=0.2),
                Gain(gain_db=3),
                Limiter(threshold_db=-0.5),
            ])
        elif "male" in voice_type:
            # 男声增强效果
            effects.extend([
                LowpassFilter(cutoff_frequency_hz=3500),
                Compressor(threshold_db=-12, ratio=2.5),
                Delay(delay_seconds=0.01, wet_level=0.1),
                Gain(gain_db=4),
                Limiter(threshold_db=-0.5),
            ])
        else:
            # RVC 默认增强效果
            effects.extend([
                HighpassFilter(cutoff_frequency_hz=150),
                Compressor(threshold_db=-20, ratio=2.5),
                Reverb(room_size=0.2, wet_level=0.15),
                Gain(gain_db=3),
                Limiter(threshold_db=-1),
            ])

        board = Pedalboard(effects)

        with AudioFile(input_audio) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        print(f"   输入采样率: {samplerate} Hz")
        print(f"   音频形状: {audio.shape}")
        print(f"   效果链: {len(effects)} 个效果")
        print(f"   正在处理...")

        effected = board(audio, samplerate)

        with AudioFile(output_audio, 'w', samplerate, effected.shape[0]) as f:
            f.write(effected)

        return True

    except Exception as e:
        print(f"❌ 增强版 Pedalboard 处理失败: {e}")
        import traceback
        traceback.print_exc()
        # 降级到基本版 pedalboard
        return change_voice_pedalboard(input_audio, output_audio, pitch_shift, voice_type)

def change_voice_rvc(input_audio, output_audio, voice_config):
    """
    使用 RVC 模型进行高质量变声
    调用独立的 RVC 推理脚本（真实版）
    强制使用 RVC，不降级
    """
    print(f"🎤 使用 RVC AI 模型进行变声...")

    model_path = voice_config.get('model_path')
    if not model_path:
        print("❌ 未配置 RVC 模型路径")
        print("   请在配置文件中设置 model_path")
        return False

    if not os.path.exists(os.path.expanduser(model_path)):
        print(f"❌ 模型文件不存在: {model_path}")
        print("   请先下载 RVC 模型")
        return False

    # 获取参数
    f0up_key = voice_config.get('f0up_key', 0)
    f0_method = voice_config.get('f0_method', 'harvest')

    print(f"   模型: {os.path.basename(model_path)}")
    print(f"   音高调整: {f0up_key:+d} 半音")

    # 检查音频时长，长音频使用分块处理
    try:
        duration = get_audio_duration(input_audio)
        print(f"   音频时长: {duration:.1f} 秒")

        # 超过 60 秒使用分块处理
        if duration > 60:
            print(f"   检测到长音频，使用分块处理...")
            script_dir = Path(__file__).parent
            rvc_process_script = script_dir / 'rvc_process_long.py'

            if not rvc_process_script.exists():
                print(f"❌ 分块处理脚本未找到: {rvc_process_script}")
                return False

            # 构建 RVC 虚拟环境路径
            skill_dir = Path(__file__).parent.parent
            rvc_env_310 = skill_dir / 'models' / 'rvc_env_310' / 'bin' / 'python3'
            rvc_env = skill_dir / 'models' / 'rvc_env' / 'bin' / 'python3'

            if rvc_env_310.exists():
                python_exe = str(rvc_env_310)
            elif rvc_env.exists():
                python_exe = str(rvc_env)
            else:
                python_exe = 'python3'

            cmd = [
                python_exe,
                str(rvc_process_script),
                input_audio,
                '-o', output_audio,
                '-m', os.path.expanduser(model_path),
                '-p', str(f0up_key)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            # 输出结果
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        print(f"   {line}")

            if result.returncode == 0 and os.path.exists(output_audio) and os.path.getsize(output_audio) > 1000:
                print(f"   ✅ RVC 分块处理成功！")
                return True
            else:
                print(f"❌ RVC 分块处理失败")
                if result.stderr:
                    for line in result.stderr.strip().split('\n')[-5:]:  # 只显示最后几行
                        if line and not line.startswith('Traceback'):
                            print(f"   {line}")
                return False

    except subprocess.TimeoutExpired:
        print("❌ 处理超时（60分钟）")
        return False
    except Exception as e:
        print(f"❌ 获取音频时长失败: {e}")
        # 继续使用普通处理

    # 普通处理（短音频或获取时长失败时）
    # 获取 RVC 推理脚本路径（使用真实 RVC 版本）
    script_dir = Path(__file__).parent
    rvc_script = script_dir / 'rvc_infer_real.py'

    if not rvc_script.exists():
        print(f"❌ RVC 推理脚本未找到: {rvc_script}")
        return False

    # 获取其他参数
    index_path = voice_config.get('index_path', '')
    index_rate = voice_config.get('index_rate', 0.75)
    filter_radius = voice_config.get('filter_radius', 3)
    resample_sr = voice_config.get('resample_sr', 0)
    rms_mix_rate = voice_config.get('rms_mix_rate', 0.25)
    protect = voice_config.get('protect', 0.33)

    if index_path:
        print(f"   Index: {os.path.basename(index_path)}")

    # 构建 RVC 虚拟环境路径（优先使用 Python 3.10 环境）
    skill_dir = Path(__file__).parent.parent
    rvc_env_310 = skill_dir / 'models' / 'rvc_env_310' / 'bin' / 'python3'
    rvc_env = skill_dir / 'models' / 'rvc_env' / 'bin' / 'python3'

    # 确定使用哪个 Python
    if rvc_env_310.exists():
        python_exe = str(rvc_env_310)
        print(f"   使用 RVC 虚拟环境 (Python 3.10)")
    elif rvc_env.exists():
        python_exe = str(rvc_env)
        print(f"   使用 RVC 虚拟环境")
    else:
        python_exe = 'python3'
        print(f"   使用系统 Python")

    # 构建命令
    cmd = [
        python_exe,
        str(rvc_script),
        input_audio,
        '-o', output_audio,
        '-m', os.path.expanduser(model_path),
        '-p', str(f0up_key),
        '-f', f0_method
    ]

    # 添加可选参数（先不使用 index 以减少内存）
    # if index_path:
    #     cmd.extend(['-i', os.path.expanduser(index_path)])
    print(f"   注意: 暂时不使用 index 文件以节省内存")
    if index_rate != 0.75:
        cmd.extend(['--index-rate', "0"])  # 不使用 index
    if filter_radius != 3:
        cmd.extend(['--filter-radius', str(filter_radius)])
    if resample_sr != 0:
        cmd.extend(['--resample-sr', str(resample_sr)])
    if rms_mix_rate != 0.25:
        cmd.extend(['--rms-mix-rate', str(rms_mix_rate)])
    if protect != 0.33:
        cmd.extend(['--protect', str(protect)])

    try:
        print(f"   正在处理...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        # 始终输出完整的结果
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")

        if result.returncode == 0:
            # 检查输出文件是否真的创建了
            if os.path.exists(output_audio) and os.path.getsize(output_audio) > 1000:
                print(f"   ✅ RVC 转换成功！")
                return True
            else:
                print(f"   ❌ RVC 返回成功但输出文件无效")
                return False
        else:
            print(f"❌ RVC 处理失败 (退出码: {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    if line and not line.startswith('Traceback') and not line.startswith('  File'):
                        print(f"   {line}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 处理超时（30分钟）")
        return False
    except Exception as e:
        print(f"❌ RVC 处理出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='音频变声处理工具')
    parser.add_argument('input_audio', help='输入音频文件路径')
    parser.add_argument('-o', '--output', help='输出音频文件路径（默认: 输入文件名_voice_changed.mp3）')
    parser.add_argument('-v', '--voice', default=None, help='目标声音类型（默认: 从配置文件读取）')
    parser.add_argument('-c', '--config', help='自定义配置文件路径')
    parser.add_argument('-m', '--method', choices=['simple', 'pedalboard', 'rvc'], default='pedalboard',
                       help='变声方法: simple(FFmpeg), pedalboard(高质量), rvc(AI模型)')
    parser.add_argument('-p', '--pitch', type=int, help='音高调整（半音，覆盖配置文件）')

    args = parser.parse_args()

    # 加载配置（早期加载以获取默认声音）
    config = load_config(args.config)

    # 确定使用的声音（命令行 > 配置文件默认值）
    if args.voice is None:
        args.voice = config.get('default_voice', 'female_1')

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

    # 检测输入是否为视频，如果是则提取音频进行处理
    input_is_video = is_video_file(args.input_audio)
    original_video = None
    temp_wav = None

    # 用于变声处理的实际输出路径（必须是音频格式）
    process_output = output_audio

    if input_is_video:
        print(f"检测到输入为视频文件，将自动处理...")
        original_video = args.input_audio
        # 创建临时 wav 文件
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='vc_')
        temp_wav = os.path.join(temp_dir, 'temp_audio.wav')
        extract_audio_from_video(args.input_audio, temp_wav)
        args.input_audio = temp_wav
        # 变声处理输出到临时 wav 文件
        process_output = os.path.join(temp_dir, 'changed_audio.wav')
        if not args.output:
            output_audio = str(Path(original_video).with_suffix('').parent / f"{Path(original_video).stem}_voice_changed.mp4")
        print(f"输出文件: {output_audio}")

    print("=" * 50)
    print("🎙️  音频变声处理")
    print("=" * 50)
    print(f"输入文件: {args.input_audio}")
    print(f"输出文件: {output_audio}")
    print(f"目标声音: {args.voice}")

    # 获取音频时长
    try:
        duration = get_audio_duration(args.input_audio)
        print(f"音频时长: {duration:.2f} 秒")
    except Exception as e:
        print(f"⚠️  无法获取音频时长: {e}")

    print()

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
    # 方法优先级: 命令行明确指定(-m) > 配置文件中声音的 method > 配置文件全局 method
    # 检查命令行是否明确指定了 -m 参数
    has_method_arg = any(arg in ['-m', '--method'] for arg in sys.argv)

    if has_method_arg:
        # 用户明确指定了方法，使用命令行参数
        method = args.method
        method_source = "命令行指定"
    else:
        # 用户没有指定，使用配置文件的方法
        config_default_method = config.get('method', 'pedalboard')
        method = voice_config.get('method', config_default_method)
        method_source = "配置文件"

    print(f"处理方法: {method} ({method_source})")

    # 获取实际的 pitch_shift（RVC 用 f0up_key）
    pitch_shift = voice_config.get('f0up_key') or voice_config.get('pitch_shift', 5)
    if args.pitch is not None:
        pitch_shift = args.pitch
        # 更新 voice_config 以便 RVC 使用
        voice_config['f0up_key'] = args.pitch

    success = False
    if method == 'simple':
        success = change_voice_simple(args.input_audio, process_output, pitch_shift)
    elif method == 'pedalboard':
        success = change_voice_pedalboard(args.input_audio, process_output, pitch_shift, args.voice)
    elif method == 'rvc':
        # 确保 f0up_key 存在
        if 'f0up_key' not in voice_config:
            voice_config['f0up_key'] = pitch_shift
        success = change_voice_rvc(args.input_audio, process_output, voice_config)

    if success:
        # 如果输入是视频，将变声后的音频合成回视频
        if input_is_video and original_video:
            print(f"\n正在合成变声后的音频与视频...")
            final_output = output_audio
            # 如果输出文件已存在，先删除
            if os.path.exists(final_output):
                os.remove(final_output)
            combine_audio_with_video(original_video, process_output, final_output)
            output_audio = final_output
            # 清理临时文件
            if temp_wav and os.path.exists(temp_wav):
                os.remove(temp_wav)
                import shutil
                shutil.rmtree(os.path.dirname(temp_wav))

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

def is_video_file(file_path):
    """检查文件是否为视频"""
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm']
    return Path(file_path).suffix.lower() in video_extensions

def extract_audio_from_video(video_file, audio_file):
    """从视频中提取音频"""
    print(f"   从视频中提取音频...")
    cmd = [
        'ffmpeg', '-y', '-i', video_file,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"提取音频失败: {result.stderr}")
    return audio_file

def combine_audio_with_video(video_file, audio_file, output_video_file):
    """将音频合成回视频"""
    print(f"   将音频合成回视频...")
    cmd = [
        'ffmpeg', '-y', '-i', video_file, '-i', audio_file,
        '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest',
        output_video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"合成视频失败: {result.stderr}")
    return output_video_file

def get_supported_format(output_path):
    """获取支持的音频格式，不支持时返回 .wav"""
    unsupported = ['.mp4', '.mov', '.avi', '.mkv']
    ext = Path(output_path).suffix.lower()
    if ext in unsupported:
        return str(Path(output_path).with_suffix('.wav'))
    return output_path

if __name__ == '__main__':
    main()
