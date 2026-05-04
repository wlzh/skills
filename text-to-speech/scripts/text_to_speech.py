#!/usr/bin/env python3
"""
Text-to-Speech Skill
将文本转换为语音，支持 Edge TTS 和 Kokoro TTS 引擎
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("no_proxy", "localhost,127.0.0.1")


class ScriptParser:
    """脚本解析器，提取实际要朗读的文本"""

    def __init__(self, config):
        self.config = config
        self.parsing_config = config.get('script_parsing', {})

    def parse(self, text):
        """解析脚本，移除注释和标记"""
        if not self.parsing_config.get('enabled', True):
            return text

        patterns = self.parsing_config.get('patterns', {})

        # 移除文件开头的标题和风格设定（第一个分隔线之前的内容）
        text = re.sub(r'^.*?-{10,}\n', '', text, flags=re.DOTALL)

        # 移除时间戳 (00:00)
        if self.parsing_config.get('remove_timestamps', True):
            text = re.sub(patterns.get('timestamps', r'\(\d{2}:\d{2}\)'), '', text)

        # 移除 BGM 注释 [BGM...] 和所有方括号内容 [...]
        if self.parsing_config.get('remove_bgm_notes', True):
            text = re.sub(patterns.get('bgm_notes', r'\[BGM[^\]]*\]'), '', text)
            text = re.sub(r'\[[^\]]*\]', '', text)

        # 移除舞台指示 (主播声音：...) (停顿 1秒) 等
        if self.parsing_config.get('remove_stage_directions', True):
            text = re.sub(patterns.get('stage_directions', r'\([^)]*(?:BGM|停顿|语速|语气|声音|强调|轻笑|准备)[^)]*\)'), '', text)

        # 移除 Markdown 加粗标记 **text**
        if self.parsing_config.get('remove_markdown', True):
            text = re.sub(patterns.get('markdown_bold', r'\*\*([^*]+)\*\*'), r'\1', text)

        # 清理多余空行和空格
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        return text


class TextToSpeech:
    """文本转语音主类，支持 Edge TTS 和 Kokoro TTS"""

    def __init__(self, config_path=None):
        self.config = self.load_config(config_path)
        self.engine = self.config.get('tts_engine', 'edge')
        self.parser = ScriptParser(self.config)

    def load_config(self, config_path):
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'tts_config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_text(self, text):
        print("📝 解析脚本...")
        parsed_text = self.parser.parse(text)
        original_lines = text.count('\n') + 1
        parsed_lines = parsed_text.count('\n') + 1
        print(f"   原始文本: {len(text)} 字符, {original_lines} 行")
        print(f"   解析后: {len(parsed_text)} 字符, {parsed_lines} 行")
        return parsed_text

    async def synthesize_edge(self, text, output_file, voice=None, rate=None, pitch=None, volume=None):
        """使用 Edge TTS 合成语音"""
        try:
            import edge_tts
        except ImportError:
            print("❌ 缺少依赖: edge-tts，请运行 pip install edge-tts")
            sys.exit(1)

        edge_config = self.config.get('edge_tts', {})
        voice = voice or edge_config.get('voice', 'zh-CN-YunyangNeural')
        rate = rate or edge_config.get('rate', '+0%')
        pitch = pitch or edge_config.get('pitch', '+0Hz')
        volume = volume or edge_config.get('volume', '+0%')

        print(f"🎤 引擎: Edge TTS")
        print(f"   声音: {voice}")
        print(f"   语速: {rate}, 音调: {pitch}, 音量: {volume}")

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        print(f"🔊 正在合成语音...")
        await communicate.save(output_file)
        print(f"✅ 语音合成完成: {output_file}")
        return output_file

    async def synthesize_kokoro(self, text, output_file, voice=None, speed=None):
        """使用 Kokoro TTS API 合成语音"""
        import requests

        kokoro_config = self.config.get('kokoro_tts', {})
        api_url = kokoro_config.get('api_url', 'http://localhost:8880/v1/audio/speech')
        voice = voice or kokoro_config.get('voice', 'zf_xiaobei')
        speed = speed or kokoro_config.get('speed', 1.0)
        fmt = kokoro_config.get('response_format', 'mp3')

        print(f"🎤 引擎: Kokoro TTS")
        print(f"   声音: {voice}")
        print(f"   语速: {speed}")
        print(f"🔊 正在合成语音...")

        try:
            resp = requests.post(
                api_url,
                json={
                    "model": "kokoro",
                    "input": text,
                    "voice": voice,
                    "response_format": fmt,
                    "speed": speed,
                },
                timeout=120,
            )
            resp.raise_for_status()
            with open(output_file, 'wb') as f:
                f.write(resp.content)
            print(f"✅ 语音合成完成: {output_file}")
            return output_file
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接 Kokoro TTS 服务，请确认容器已启动: cd kokoro-tts && ./start.sh")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ Kokoro TTS API 错误: {e}")
            print(f"   响应: {resp.text[:300]}")
            return None

    async def synthesize(self, text, output_file, voice=None, rate=None, pitch=None, volume=None, speed=None):
        """根据引擎选择合成方式"""
        if self.engine == 'kokoro':
            return await self.synthesize_kokoro(text, output_file, voice, speed)
        else:
            return await self.synthesize_edge(text, output_file, voice, rate, pitch, volume)

    def post_process(self, audio_file):
        post_config = self.config.get('post_processing', {})
        if not post_config.get('enabled', False):
            return audio_file

        voice_changer_config = post_config.get('voice_changer', {})
        if not voice_changer_config.get('enabled', False):
            return audio_file

        print("🎵 开始后处理（voice-changer）...")
        voice_changer_script = Path.home() / '.claude' / 'skills' / 'voice-changer' / 'scripts' / 'voice_change.py'

        if not voice_changer_script.exists():
            print("⚠️  voice-changer skill 未找到，跳过后处理")
            return audio_file

        voice_type = voice_changer_config.get('voice_type', 'female_1')
        pitch_shift = voice_changer_config.get('pitch_shift', None)
        output_file = audio_file.replace('.mp3', '_voice_changed.mp3')

        import subprocess
        cmd = ['python3', str(voice_changer_script), audio_file, '-v', voice_type, '-o', output_file]
        if pitch_shift is not None:
            cmd.extend(['-p', str(pitch_shift)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 后处理完成: {output_file}")
            return output_file
        else:
            print(f"⚠️  后处理失败: {result.stderr}")
            return audio_file

    def get_output_path(self, input_text_file, output_file=None):
        output_config = self.config.get('output', {})
        if output_file:
            return output_file
        if input_text_file and os.path.isfile(input_text_file):
            input_path = Path(input_text_file)
            suffix = output_config.get('filename_suffix', '_tts')
            output_file = input_path.parent / f"{input_path.stem}{suffix}.mp3"
        else:
            suffix = output_config.get('filename_suffix', '_tts')
            output_file = f"output{suffix}.mp3"
        return str(output_file)

    async def convert(self, input_source, output_file=None, voice=None, rate=None, pitch=None, volume=None, speed=None):
        print("=" * 60)
        print("🎙️  Text-to-Speech")
        print("=" * 60)

        if os.path.isfile(input_source):
            print(f"📄 读取文本文件: {input_source}")
            with open(input_source, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            print(f"📝 使用输入文本")
            text = input_source

        parsed_text = self.parse_text(text)
        if not parsed_text.strip():
            print("❌ 错误: 解析后的文本为空")
            return None

        output_file = self.get_output_path(
            input_source if os.path.isfile(input_source) else None,
            output_file
        )

        audio_file = await self.synthesize(parsed_text, output_file, voice, rate, pitch, volume, speed)
        if audio_file is None:
            return None

        final_file = self.post_process(audio_file)

        print("=" * 60)
        print(f"✅ 完成！输出文件: {final_file}")
        print("=" * 60)
        return final_file


def main():
    parser = argparse.ArgumentParser(
        description='Text-to-Speech - 将文本转换为语音（支持 Edge TTS / Kokoro TTS）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从文件转换
  python3 text_to_speech.py script.txt

  # 使用 Kokoro 引擎
  python3 text_to_speech.py script.txt --engine kokoro

  # 指定声音
  python3 text_to_speech.py script.txt -v zf_xiaobei

  # 列出所有可用声音
  python3 text_to_speech.py --list-voices

  # 从标准输入读取
  echo "你好，世界" | python3 text_to_speech.py -
        """
    )

    parser.add_argument('input', nargs='?', help='输入文本文件路径（或使用 - 从标准输入读取）')
    parser.add_argument('-o', '--output', help='输出音频文件路径')
    parser.add_argument('-c', '--config', help='配置文件路径')
    parser.add_argument('-e', '--engine', choices=['edge', 'kokoro'], help='TTS 引擎（覆盖配置文件）')
    parser.add_argument('-v', '--voice', help='声音类型')
    parser.add_argument('--rate', help='语速调整（Edge TTS: 如 +20%%）')
    parser.add_argument('--pitch', help='音调调整（Edge TTS: 如 +5Hz）')
    parser.add_argument('--volume', help='音量调整（Edge TTS: 如 +20%%）')
    parser.add_argument('--speed', type=float, help='语速（Kokoro: 如 1.0）')
    parser.add_argument('--post-process', action='store_true', help='启用后处理（voice-changer）')
    parser.add_argument('--list-voices', action='store_true', help='列出所有可用的声音')

    args = parser.parse_args()

    tts = TextToSpeech(args.config)

    # 命令行参数覆盖配置文件中的引擎
    if args.engine:
        tts.engine = args.engine

    if args.list_voices:
        all_voices = tts.config.get('available_voices', {})
        for engine_name, voices in all_voices.items():
            print(f"\n[{engine_name}]")
            print("-" * 60)
            for voice, desc in voices.items():
                print(f"  {voice:<30} {desc}")
        return

    if not args.input:
        parser.print_help()
        return

    if args.input == '-':
        input_text = sys.stdin.read()
    else:
        input_text = args.input

    if args.post_process:
        tts.config['post_processing']['enabled'] = True
        tts.config['post_processing']['voice_changer']['enabled'] = True

    asyncio.run(tts.convert(
        input_text,
        args.output,
        args.voice,
        args.rate,
        args.pitch,
        args.volume,
        args.speed,
    ))


if __name__ == '__main__':
    main()
