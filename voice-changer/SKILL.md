---
name: voice-changer
description: 音频变声处理工具 - 使用 RVC AI 模型进行真实的声音转换
version: 1.5.0
author: M.
---

# voice-changer Skill

## 概述

voice-changer 是一个音频变声处理 skill，使用 RVC AI 模型进行真实的音色转换（不只是音高调整）。

## 功能特性

- 🎙️ **RVC AI 模型** - 真实的音色转换
- ⚡ **自动分块处理** - 长音频自动分块，避免内存问题
- 🔧 **灵活配置** - 支持多种声音预设和自定义参数
- 🎯 **简单易用**: 命令行一键调用
- 🔌 **可被调用** - 可被其他 skills 集成调用

## 技术方案

### 当前实现: RVC 方法（AI 模型）

**优点:**
- 真实的音色转换（不只是音高调整）
- 音质自然，效果更好
- 可以真正"克隆"声音
- 支持跨语言

**原理:**
使用 HuBERT 特征提取 + RVC 模型推理：
1. HuBERT 提取音频特征
2. F0 提取基频
3. RVC 模型进行声音转换
4. 长音频自动分块处理

**适用场景:**
- 高质量变声需求
- 需要真实音色转换
- 播客、配音等场景

## 目录结构

```
voice-changer/
├── SKILL.md              # 本文档
├── README.md             # 使用说明
├── scripts/
│   └── voice_change.py   # 核心变声脚本
├── config/
│   └── voice_config.json # 声音配置文件
└── models/               # RVC 模型目录
    ├── rvc_env_310/      # Python 3.10 环境
    ├── rvc_core/         # RVC 核心代码
    └── rvc_models/       # RVC 模型文件
```

## 依赖要求

### 必需依赖
- Python 3.10（RVC 兼容性）
- FFmpeg 4.0+
- FFprobe

### Python 依赖（已包含在 rvc_env_310/）
- torch==2.5.1
- fairseq==0.12.2
- librosa
- soundfile
- pyworld
- parselmouth
- faiss-cpu
- torchcrepe
- pedalboard

## 配置说明

### voice_config.json 结构

```json
{
  "method": "rvc",
  "rvc_model_path": "models/rvc_models/trained_models/kohane.pth",
  "default_voice": "female_3",
  "voices": {
    "female_3": {
      "name": "女声（甜美）",
      "method": "rvc",
      "model_path": "...kohane.pth",
      "index_path": "...kohane.index",
      "f0up_key": -1,
      "f0_method": "harvest"
    }
  }
}
```

### 参数说明

- `method`: 处理方法（`rvc` 或 `pedalboard`）
- `f0up_key`: 音高调整（半音）
  - 正值: 提高音调（女声效果）
  - 负值: 降低音调（男声效果）
  - 范围: -12 到 +12
- `f0_method`: F0 提取方法（`harvest`、`crepe`、`pm` 等）

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

| 预设名称 | 音高 | 描述 | 适用场景 |
|---------|------|------|---------|
| female_1 | 0 | 女声（轻柔） | 基础女声 |
| female_2 | +2 | 女声（明亮） | 更高的女声 |
| female_3 | -1 | 女声（甜美）⭐ | **默认**，自然女声 |
| child | +8 | 童声 | 儿童效果 |
| rvc_female | +4 | AI 女声（高音高） | 高质量女声 |
| rvc_male | -12 | AI 男声（低音高） | 高质量男声 |
| male_normal | -8 | 男声（正常） | 自然男声 |
| male_deep | -12 | 男声（低沉） | 低沉男声 |

## 性能指标

### RVC 方法（CPU 模式，Apple Silicon M1）
- 短音频 (< 60秒): ~10-30 秒
- 长音频分块处理: ~3-5 分钟（15 分钟音频）
- 超长音频 (875秒): ~15 分钟（32 段处理）

### 内存占用
- 短音频: < 500MB
- 长音频分块: 自动管理，避免 OOM

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

1. **处理时间**: RVC 方法处理速度较慢，CPU 模式需要耐心等待
2. **长音频**: 自动分块处理，超长音频可能需要较长时间
3. **文件格式**: 支持常见音频格式（MP3, WAV, M4A 等）
4. **版权问题**: 请确保有权对音频进行处理和使用
5. **模型资源**: 更多 RVC 模型可参考 [260款RVC变声器模型](https://pan.quark.cn/s/1cf1c5d6d4a6)

## 故障排除

### 问题 1: FFmpeg 未安装
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 问题 2: 处理速度慢
- CPU 模式处理较慢是正常的
- 如有 GPU 可修改代码使用 CUDA
- 短音频处理较快（~10-30 秒）

### 问题 3: 内存不足
- 已自动分块处理，长音频不会 OOM
- 如仍有问题，可减小分块大小

### 问题 4: 音质不佳
- 确保使用高质量输入音频
- 尝试不同的 f0up_key 值
- 考虑下载更多 RVC 模型尝试

## 未来计划

- [ ] 添加更多音效（回声、混响等）
- [ ] 支持批量处理
- [ ] 添加 GUI 界面
- [ ] 支持实时变声
- [ ] GPU 加速支持

## 参考资料

- [FFmpeg 音频滤镜文档](https://ffmpeg.org/ffmpeg-filters.html#Audio-Filters)
- [RVC 项目](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
- [音高与频率关系](https://en.wikipedia.org/wiki/Pitch_(music))
