#!/usr/bin/env python3
"""
音频关键字过滤主流程
根据关键字配置文件识别并删除音频中的关键字片段
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 导入子模块
sys.path.insert(0, str(Path(__file__).parent))
from transcribe_audio import transcribe_with_funasr
from detect_keywords import load_keywords, find_keyword_positions, generate_delete_plan
from cut_audio import cut_audio


def main():
    parser = argparse.ArgumentParser(description='音频关键字过滤工具')
    parser.add_argument('input_audio', help='输入音频文件')
    parser.add_argument('-o', '--output', help='输出音频文件（默认：输入文件名_filtered.mp3）')
    parser.add_argument('-k', '--keywords', help='关键字配置文件（默认：config/keywords.json）')
    parser.add_argument('--buffer-before', type=float, default=0.5, help='删除前缓冲时间（秒）')
    parser.add_argument('--buffer-after', type=float, default=0.5, help='删除后缓冲时间（秒）')
    parser.add_argument('--keep-transcript', action='store_true', help='保留转录文件')
    parser.add_argument('--change-voice', help='变声处理（如: female_1, female_2, male_deep）')

    args = parser.parse_args()

    # 设置路径
    input_audio = Path(args.input_audio)
    if not input_audio.exists():
        print(f"❌ 错误: 文件不存在 {input_audio}")
        sys.exit(1)

    # 输出文件
    if args.output:
        output_audio = Path(args.output)
    else:
        output_audio = input_audio.parent / f"{input_audio.stem}_filtered{input_audio.suffix}"

    # 关键字配置文件
    if args.keywords:
        keywords_file = Path(args.keywords)
    else:
        keywords_file = Path(__file__).parent.parent / 'config' / 'keywords.json'

    if not keywords_file.exists():
        print(f"❌ 错误: 关键字配置文件不存在 {keywords_file}")
        sys.exit(1)

    print("=" * 60)
    print("🎵 音频关键字过滤工具")
    print("=" * 60)
    print(f"输入音频: {input_audio}")
    print(f"输出音频: {output_audio}")
    print(f"关键字配置: {keywords_file}")
    print("=" * 60)

    # 步骤 1: 转录音频
    total_steps = 5 if args.change_voice else 4
    print(f"\n📝 步骤 1/{total_steps}: 转录音频...")
    transcript_file = input_audio.parent / f"{input_audio.stem}_transcript.json"
    transcript_data = transcribe_with_funasr(str(input_audio), str(transcript_file))

    # 步骤 2: 加载关键字
    print(f"\n📋 步骤 2/{total_steps}: 加载关键字配置...")
    keywords = load_keywords(str(keywords_file))
    print(f"   加载了 {len(keywords)} 个关键字")

    # 步骤 3: 查找关键字
    print(f"\n🔍 步骤 3/{total_steps}: 查找关键字...")
    matches = find_keyword_positions(transcript_data, keywords)

    if not matches:
        print("✅ 未找到任何关键字，无需处理")
        print(f"   原始音频: {input_audio}")
        sys.exit(0)

    # 生成删除计划
    print(f"\n📊 生成删除计划...")
    delete_segments = generate_delete_plan(
        matches,
        buffer_before=args.buffer_before,
        buffer_after=args.buffer_after
    )

    print(f"   合并后删除片段数: {len(delete_segments)}")
    for i, (start, end) in enumerate(delete_segments, 1):
        print(f"   {i}. {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")

    # 保存删除计划
    delete_plan_file = input_audio.parent / f"{input_audio.stem}_delete_plan.json"
    with open(delete_plan_file, 'w', encoding='utf-8') as f:
        json.dump({
            'delete_segments': delete_segments,
            'total_duration': transcript_data['duration'],
            'matches': matches
        }, f, ensure_ascii=False, indent=2)

    # 步骤 4: 执行剪辑
    print(f"\n✂️  步骤 4/{total_steps}: 执行剪辑...")
    success = cut_audio(
        str(input_audio),
        str(output_audio),
        delete_segments,
        transcript_data['duration']
    )

    if success:
        # 步骤 5: 变声处理（可选）
        final_output = output_audio
        if args.change_voice:
            print("\n🎤 步骤 5/5: 变声处理...")
            print(f"   目标声音: {args.change_voice}")

            voice_changer_script = Path.home() / '.claude' / 'skills' / 'voice-changer' / 'scripts' / 'voice_change.py'

            if not voice_changer_script.exists():
                print(f"⚠️  警告: voice-changer skill 未安装，跳过变声处理")
            else:
                import subprocess

                voice_output = output_audio.parent / f"{output_audio.stem}_voice_changed{output_audio.suffix}"

                cmd = [
                    'python3', str(voice_changer_script),
                    str(output_audio),
                    '-v', args.change_voice,
                    '-o', str(voice_output)
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✅ 变声完成: {voice_output}")
                    final_output = voice_output
                else:
                    print(f"⚠️  变声失败，使用原始过滤后的音频")
                    print(f"   错误: {result.stderr}")

        print("\n" + "=" * 60)
        print("✅ 处理完成！")
        print("=" * 60)
        print(f"最终输出: {final_output}")
        if args.change_voice and final_output != output_audio:
            print(f"过滤音频: {output_audio}")
        print(f"删除计划: {delete_plan_file}")
        if args.keep_transcript:
            print(f"转录文件: {transcript_file}")
        else:
            # 清理转录文件
            if transcript_file.exists():
                transcript_file.unlink()
        print("=" * 60)
    else:
        print("\n❌ 处理失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
