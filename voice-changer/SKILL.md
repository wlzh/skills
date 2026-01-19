---
name: voice-changer
description: 音频变声处理工具 - 将音频转换为不同的声音效果（如女声、男声、童声等）
version: 1.0.0
author: M.
---

# voice-changer Skill

## 概述

voice-changer 是一个音频变声处理 skill，可以将音频转换为不同的声音效果（如女声、男声、童声等）。

## 功能特性

- 🎵 **多种声音预设**: 支持女声、男声、童声等多种预设
- ⚡ **快速处理**: 使用 FFmpeg 进行音高调整，处理速度快
- 🔧 **灵活配置**: 支持自定义音高调整参数
- 🎯 **简单易用**: 命令行一键调用
- 🔌 **模块化设计**: 可被其他 skills 调用集成

## 技术方案

### 当前实现: Simple 方法（FFmpeg 音高调整）

**优点:**
- 无需额外模型，依赖少
- 处理速度快（接近实时）
- 资源占用低

**原理:**
使用 FFmpeg 的 `asetrate` + `aresample` + `atempo` 滤镜组合：
1. 调整采样率改变音高
2. 重采样恢复原采样率
3. 调整播放速度保持时长不变

**适用场景:**
- 快速变声需求
- 资源受限环境
- 批量处理

### 未来扩展: RVC 方法（AI 模型）

**优点:**
- 音质更自然
- 可以真正"克隆"声音
- 支持跨语言

**缺点:**
- 需要额外模型（50-200MB）
- 处理速度较慢
- 需要 GPU 加速

## 目录结构

```
voice-changer/
├── SKILL.md              # 本文档
├── README.md             # 使用说明
├── scripts/
│   └── voice_change.py   # 核心变声脚本
├── config/
│   └── voice_config.json # 声音配置文件
└── models/               # AI 模型目录（未来使用）
```

## 依赖要求

### 必需依赖
- Python 3.8+
- FFmpeg 4.0+
- FFprobe

### 可选依赖（RVC 方法）
- PyTorch
- librosa
- soundfile
- RVC 相关库

## 配置说明

### voice_config.json 结构

```json
{
  "method": "simple",
  "voices": {
    "female_1": {
      "name": "女声 1（轻柔）",
      "pitch_shift": 5,
      "description": "音调提高 5 个半音"
    }
  },
  "default_voice": "female_1"
}
```

### 参数说明

- `method`: 处理方法（`simple` 或 `rvc`）
- `pitch_shift`: 音高调整（半音）
  - 正值: 提高音调（女声效果）
  - 负值: 降低音调（男声效果）
  - 范围: -12 到 +12

## 使用方法

### 1. 独立使用

```bash
# 基本用法（使用默认女声）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3

# 指定声音类型
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -v female_2

# 指定输出文件
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -o output.mp3

# 自定义音高
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -p 7

# 查看帮助
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py --help
```

### 2. 在其他 Skills 中调用

```python
import subprocess

def change_voice(input_audio, voice_type='female_1'):
    """调用 voice-changer skill"""
    script_path = os.path.expanduser(
        '~/.claude/skills/voice-changer/scripts/voice_change.py'
    )

    output_audio = input_audio.replace('.mp3', '_voice_changed.mp3')

    cmd = [
        'python3', script_path,
        input_audio,
        '-v', voice_type,
        '-o', output_audio
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return output_audio
    else:
        print(f"变声失败: {result.stderr}")
        return input_audio
```

## 预设声音列表

| 预设名称 | 音高偏移 | 描述 | 适用场景 |
|---------|---------|------|---------|
| female_1 | +5 | 女声（轻柔） | 男声转女声 |
| female_2 | +7 | 女声（明亮） | 更高的女声 |
| female_3 | +4 | 女声（甜美） | 自然女声 |
| male_deep | -5 | 男声（低沉） | 女声转男声 |
| male_normal | -3 | 男声（正常） | 自然男声 |
| child | +8 | 童声 | 儿童效果 |
| robot | 0 | 机器人 | 特殊效果 |

## 性能指标

### Simple 方法
- 处理速度: ~1-2x 实时率
- 内存占用: < 100MB
- CPU 占用: 中等

### 示例（14 分钟音频）
- 输入: 14MB MP3
- 处理时间: ~7-14 秒
- 输出: 14MB MP3

## 集成示例

### 与 audiocut-keyword 集成

```bash
# 先过滤关键字，再变声
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py input.mp3 --change-voice female_1
```

### 与 youtube-to-xiaoyuzhou 集成

```bash
# YouTube 下载 + 过滤 + 变声 + 发布
python3 ~/.claude/skills/youtube-to-xiaoyuzhou/youtube_to_xiaoyuzhou.py \
  https://youtu.be/xxxxx \
  --filter-keywords \
  --change-voice female_1 \
  --schedule "2026-01-20 18:00"
```

## 注意事项

1. **音质损失**: 音高调整会带来一定的音质损失，调整幅度越大损失越明显
2. **处理时间**: 长音频处理需要一定时间，建议先用短音频测试
3. **文件格式**: 支持常见音频格式（MP3, WAV, M4A 等）
4. **版权问题**: 请确保有权对音频进行处理和使用

## 故障排除

### 问题 1: FFmpeg 未安装
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 问题 2: 音质不理想
- 尝试调整 `pitch_shift` 参数
- 使用更小的调整幅度
- 考虑使用 RVC 方法（需额外配置）

### 问题 3: 处理速度慢
- 检查 CPU 占用
- 减少同时处理的文件数量
- 考虑使用更短的音频片段

## 未来计划

- [ ] 集成 RVC 模型支持
- [ ] 添加更多音效（回声、混响等）
- [ ] 支持批量处理
- [ ] 添加 GUI 界面
- [ ] 支持实时变声

## 参考资料

- [FFmpeg 音频滤镜文档](https://ffmpeg.org/ffmpeg-filters.html#Audio-Filters)
- [RVC 项目](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
- [音高与频率关系](https://en.wikipedia.org/wiki/Pitch_(music))
