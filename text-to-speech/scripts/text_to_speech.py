#!/usr/bin/env python3
"""
Text-to-Speech Skill
将文本转换为语音，支持脚本解析和情绪标记
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("❌ 缺少依赖: edge-tts")
    print("请运行: pip install edge-tts")
    sys.exit(1)


class ScriptParser:
    """脚本解析器，提取实际要朗读的文本"""

    def __init__(self, config):
        self.config = config
        self.parsing_config = config.get('script_parsing', {})

    def parse(self, text):
        """解析脚本，移除注释和标记"""
        if not self.parsing_config.get('enabled', True):
            return text

        original_text = text
        patterns = self.parsing_config.get('patterns', {})

        # 移除文件开头的标题和风格设定（第一个分隔线之前的内容）
        text = re.sub(r'^.*?-{10,}\n', '', text, flags=re.DOTALL)

        # 移除时间戳 (00:00)
        if self.parsing_config.get('remove_timestamps', True):
            text = re.sub(patterns.get('timestamps', r'\(\d{2}:\d{2}\)'), '', text)

        # 移除 BGM 注释 [BGM...] 和所有方括号内容 [...]
        if self.parsing_config.get('remove_bgm_notes', True):
            text = re.sub(patterns.get('bgm_notes', r'\[BGM[^\]]*\]'), '', text)
            # 移除所有方括号内的导演指示
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

    def extract_emotions(self, text):
        """提取情绪标记（用于 SSML 处理）"""
        emotions = []
        # 这里可以扩展提取情绪标记的逻辑
        return emotions


class SSMLGenerator:
    """SSML 生成器，根据情绪标记生成 SSML"""

    def __init__(self, config):
        self.config = config
        self.emotion_config = config.get('emotion_processing', {})

    def generate(self, text):
        """生成 SSML 标记的文本"""
        if not self.emotion_config.get('enabled', True):
            return text

        if not self.emotion_config.get('use_ssml', True):
            return text

        # 目前先返回纯文本，后续可以扩展 SSML 支持
        # Edge TTS 的 SSML 支持有限，主要通过 rate/pitch/volume 参数控制
        return text


class TextToSpeech:
    """文本转语音主类"""

    def __init__(self, config_path=None):
        self.config = self.load_config(config_path)
        self.parser = ScriptParser(self.config)
        self.ssml_generator = SSMLGenerator(self.config)

    def load_config(self, config_path):
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'tts_config.json'

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_text(self, text):
        """解析文本"""
        print("📝 解析脚本...")
        parsed_text = self.parser.parse(text)

        # 显示解析前后对比
        original_lines = text.count('\n') + 1
        parsed_lines = parsed_text.count('\n') + 1
        print(f"   原始文本: {len(text)} 字符, {original_lines} 行")
        print(f"   解析后: {len(parsed_text)} 字符, {parsed_lines} 行")

        return parsed_text

    async def synthesize(self, text, output_file, voice=None, rate=None, pitch=None, volume=None):
        """合成语音"""
        # 使用配置或参数指定的声音
        edge_config = self.config.get('edge_tts', {})
        voice = voice or edge_config.get('voice', 'zh-CN-YunyangNeural')
        rate = rate or edge_config.get('rate', '+0%')
        pitch = pitch or edge_config.get('pitch', '+0Hz')
        volume = volume or edge_config.get('volume', '+0%')

        print(f"🎤 使用声音: {voice}")
        print(f"   语速: {rate}, 音调: {pitch}, 音量: {volume}")

        # 创建 TTS 通信对象
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)

        print(f"🔊 正在合成语音...")
        await communicate.save(output_file)
        print(f"✅ 语音合成完成: {output_file}")

        return output_file

    def post_process(self, audio_file):
        """后处理：调用 voice-changer"""
        post_config = self.config.get('post_processing', {})

        if not post_config.get('enabled', False):
            return audio_file

        voice_changer_config = post_config.get('voice_changer', {})
        if not voice_changer_config.get('enabled', False):
            return audio_file

        print("🎵 开始后处理（voice-changer）...")

        # 调用 voice-changer
        voice_changer_script = Path.home() / '.claude' / 'skills' / 'voice-changer' / 'scripts' / 'voice_change.py'

        if not voice_changer_script.exists():
            print("⚠️  voice-changer skill 未找到，跳过后处理")
            return audio_file

        voice_type = voice_changer_config.get('voice_type', 'female_1')
        pitch_shift = voice_changer_config.get('pitch_shift', None)

        output_file = audio_file.replace('.mp3', '_voice_changed.mp3')

        import subprocess
        cmd = [
            'python3', str(voice_changer_script),
            audio_file,
            '-v', voice_type,
            '-o', output_file
        ]

        # 只有明确指定了 pitch_shift 时才传递 -p 参数
        # 否则使用 voice_type 预设的 pitch_shift
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
        """确定输出文件路径"""
        output_config = self.config.get('output', {})

        if output_file:
            return output_file

        # 如果输入是文件，使用相同目录
        if input_text_file and os.path.isfile(input_text_file):
            input_path = Path(input_text_file)
            suffix = output_config.get('filename_suffix', '_tts')
            output_file = input_path.parent / f"{input_path.stem}{suffix}.mp3"
        else:
            # 如果输入是文本，使用当前目录
            suffix = output_config.get('filename_suffix', '_tts')
            output_file = f"output{suffix}.mp3"

        return str(output_file)

    async def convert(self, input_source, output_file=None, voice=None, rate=None, pitch=None, volume=None):
        """转换文本为语音"""
        print("=" * 60)
        print("🎙️  Text-to-Speech")
        print("=" * 60)

        # 读取输入文本
        if os.path.isfile(input_source):
            print(f"📄 读取文本文件: {input_source}")
            with open(input_source, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            print(f"📝 使用输入文本")
            text = input_source

        # 解析脚本
        parsed_text = self.parse_text(text)

        if not parsed_text.strip():
            print("❌ 错误: 解析后的文本为空")
            return None

        # 确定输出路径
        output_file = self.get_output_path(
            input_source if os.path.isfile(input_source) else None,
            output_file
        )

        # 合成语音
        audio_file = await self.synthesize(parsed_text, output_file, voice, rate, pitch, volume)

        # 后处理
        final_file = self.post_process(audio_file)

        print("=" * 60)
        print(f"✅ 完成！输出文件: {final_file}")
        print("=" * 60)

        return final_file


def main():
    parser = argparse.ArgumentParser(
        description='Text-to-Speech - 将文本转换为语音',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从文件转换
  python3 text_to_speech.py script.txt

  # 指定输出文件
  python3 text_to_speech.py script.txt -o output.mp3

  # 指定声音
  python3 text_to_speech.py script.txt -v zh-CN-XiaoxiaoNeural

  # 调整语速和音调
  python3 text_to_speech.py script.txt --rate "+20%" --pitch "+5Hz"

  # 从标准输入读取
  echo "你好，世界" | python3 text_to_speech.py -

  # 启用后处理（voice-changer）
  python3 text_to_speech.py script.txt --post-process
        """
    )

    parser.add_argument('input', help='输入文本文件路径（或使用 - 从标准输入读取）')
    parser.add_argument('-o', '--output', help='输出音频文件路径')
    parser.add_argument('-c', '--config', help='配置文件路径')
    parser.add_argument('-v', '--voice', help='声音类型（如 zh-CN-YunyangNeural）')
    parser.add_argument('--rate', help='语速调整（如 +20%% 或 -10%%）')
    parser.add_argument('--pitch', help='音调调整（如 +5Hz 或 -3Hz）')
    parser.add_argument('--volume', help='音量调整（如 +20%% 或 -10%%）')
    parser.add_argument('--post-process', action='store_true', help='启用后处理（voice-changer）')
    parser.add_argument('--list-voices', action='store_true', help='列出所有可用的声音')

    args = parser.parse_args()

    # 创建 TTS 对象
    tts = TextToSpeech(args.config)

    # 列出可用声音
    if args.list_voices:
        print("可用的声音:")
        print("-" * 60)
        available_voices = tts.config.get('available_voices', {})
        for voice, desc in available_voices.items():
            print(f"  {voice:<30} {desc}")
        return

    # 读取输入
    if args.input == '-':
        input_text = sys.stdin.read()
    else:
        input_text = args.input

    # 如果启用后处理，修改配置
    if args.post_process:
        tts.config['post_processing']['enabled'] = True
        tts.config['post_processing']['voice_changer']['enabled'] = True

    # 转换
    asyncio.run(tts.convert(
        input_text,
        args.output,
        args.voice,
        args.rate,
        args.pitch,
        args.volume
    ))


if __name__ == '__main__':
    main()
