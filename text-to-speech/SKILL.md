---
name: text-to-speech
description: 文本转语音工具 - 支持脚本解析、情绪标记和后处理，基于 Edge TTS
version: 1.0.0
author: M.
---

# Text-to-Speech Skill

将文本转换为语音，支持播客脚本解析、情绪标记处理和 voice-changer 后处理。

## 使用说明

当用户请求将文本转换为语音时，使用以下命令：

```bash
# 基本用法
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py <文本文件>

# 指定输出文件
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -o output.mp3

# 指定声音
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -v zh-CN-XiaoxiaoNeural

# 启用后处理（voice-changer）
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --post-process

# 列出所有可用声音
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py --list-voices
```

## 核心功能

### 1. 脚本解析
自动识别并移除播客脚本中的注释和标记：
- 时间戳：`(00:00)`
- BGM 注释：`[BGM渐入：...]`
- 舞台指示：`(主播声音：...)` `(停顿 1秒)`
- 情绪标记：`(语速放慢，加重语气)`
- Markdown 标记：`**文本**`

### 2. 多种声音支持
支持 18+ 种中文声音，包括：
- **男声**：YunyangNeural（新闻播音）、YunxiNeural（年轻活力）、YunjianNeural（成熟稳重）
- **女声**：XiaoxiaoNeural（温柔亲切）、XiaoyiNeural（活泼开朗）、XiaoyanNeural（新闻播音）

### 3. 语音参数调整
- 语速调整：`--rate "+20%"` 或 `--rate "-10%"`
- 音调调整：`--pitch "+5Hz"` 或 `--pitch "-3Hz"`
- 音量调整：`--volume "+20%"` 或 `--volume "-10%"`

### 4. 后处理集成
可选集成 voice-changer skill 进行变声处理。

## 配置文件

配置文件位于：`~/.claude/skills/text-to-speech/config/tts_config.json`

### 主要配置项

```json
{
  "edge_tts": {
    "voice": "zh-CN-YunyangNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "volume": "+0%"
  },
  "script_parsing": {
    "enabled": true,
    "remove_timestamps": true,
    "remove_bgm_notes": true,
    "remove_stage_directions": true,
    "remove_markdown": true
  },
  "emotion_processing": {
    "enabled": true,
    "use_ssml": true
  },
  "output": {
    "format": "mp3",
    "default_output_dir": "same_as_input",
    "filename_suffix": "_tts"
  },
  "post_processing": {
    "enabled": false,
    "voice_changer": {
      "enabled": false,
      "voice_type": "female_1",
      "pitch_shift": 0
    }
  }
}
```

## 工作流程

```
输入文本/文件
    ↓
脚本解析（移除注释和标记）
    ↓
情绪标记处理（可选）
    ↓
Edge TTS 语音合成
    ↓
后处理（voice-changer，可选）
    ↓
输出 MP3 文件
```

## 依赖安装

```bash
# 安装 Edge TTS
pip install edge-tts

# 如果需要后处理，确保 voice-changer skill 已安装
```

## 使用示例

### 示例 1：转换播客脚本

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py podcast_script.txt
```

脚本会自动：
- 移除时间戳和 BGM 注释
- 移除舞台指示
- 只保留实际要朗读的文本
- 生成 `podcast_script_tts.mp3`

### 示例 2：使用女声并调整语速

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt \
  -v zh-CN-XiaoxiaoNeural \
  --rate "+10%"
```

### 示例 3：启用后处理

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt \
  --post-process
```

会先生成语音，然后调用 voice-changer 进行变声处理。

## 注意事项

1. **网络要求**：Edge TTS 需要网络连接
2. **文本长度**：建议单次转换不超过 10000 字
3. **脚本格式**：支持纯文本和带注释的播客脚本
4. **后处理**：需要先安装 voice-changer skill

## 技术实现

- **TTS 引擎**：Microsoft Edge TTS（免费、高质量）
- **脚本解析**：正则表达式匹配
- **音频格式**：MP3（默认）
- **后处理**：可选集成 voice-changer

## 性能参考

- 1000 字文本：约 10-20 秒
- 5000 字文本：约 30-60 秒
- 网络速度影响较大

## 许可

MIT
