# voice-changer

> 版本: v1.0.0

音频变声处理工具 - 将音频转换为不同的声音效果

## 快速开始

```bash
# 基本用法（转换为女声）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3

# 指定声音类型
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -v female_2

# 自定义音高（+7 半音）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -p 7
```

## 功能特性

- 🎵 多种声音预设（女声、男声、童声等）
- ⚡ 快速处理（基于 FFmpeg）
- 🔧 灵活配置
- 🔌 可被其他 skills 调用

## 安装依赖

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# 验证安装
ffmpeg -version
```

## 声音预设

| 预设 | 音高 | 描述 |
|-----|------|------|
| female_1 | +5 | 女声（轻柔） |
| female_2 | +7 | 女声（明亮） |
| female_3 | +4 | 女声（甜美） |
| male_deep | -5 | 男声（低沉） |
| male_normal | -3 | 男声（正常） |
| child | +8 | 童声 |

## 命令行参数

```
usage: voice_change.py [-h] [-o OUTPUT] [-v VOICE] [-c CONFIG]
                       [-m {simple,rvc}] [-p PITCH] input_audio

参数:
  input_audio           输入音频文件
  -o, --output         输出文件路径
  -v, --voice          声音类型（默认: female_1）
  -c, --config         自定义配置文件
  -m, --method         处理方法: simple 或 rvc
  -p, --pitch          音高调整（半音）
```

## 使用示例

### 示例 1: 男声转女声
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  male_voice.mp3 \
  -v female_1 \
  -o female_voice.mp3
```

### 示例 2: 自定义音高
```bash
# 提高 6 个半音
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  input.mp3 \
  -p 6
```

### 示例 3: 批量处理
```bash
for file in *.mp3; do
  python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
    "$file" \
    -v female_1
done
```

## 集成到其他 Skills

### 在 Python 中调用

```python
import subprocess
import os

def change_voice(input_audio, voice_type='female_1'):
    script = os.path.expanduser(
        '~/.claude/skills/voice-changer/scripts/voice_change.py'
    )
    output = input_audio.replace('.mp3', '_voice_changed.mp3')

    cmd = ['python3', script, input_audio, '-v', voice_type, '-o', output]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return output if result.returncode == 0 else input_audio
```

### 在 Bash 中调用

```bash
#!/bin/bash
VOICE_CHANGER="$HOME/.claude/skills/voice-changer/scripts/voice_change.py"

# 变声处理
python3 "$VOICE_CHANGER" input.mp3 -v female_1
```

## 配置文件

编辑 `config/voice_config.json` 自定义声音预设:

```json
{
  "voices": {
    "my_voice": {
      "name": "我的自定义声音",
      "pitch_shift": 6,
      "description": "自定义音高"
    }
  }
}
```

## 性能参考

- 14 分钟音频: ~7-14 秒处理时间
- 内存占用: < 100MB
- CPU 占用: 中等

## 注意事项

1. 音高调整幅度越大，音质损失越明显
2. 建议音高调整范围: -12 到 +12 半音
3. 支持格式: MP3, WAV, M4A, FLAC 等

## 故障排除

**问题: 音质不佳**
- 减小音高调整幅度
- 使用高质量输入音频

**问题: 处理失败**
- 检查 FFmpeg 是否正确安装
- 确认输入文件格式正确

## 更新记录

### v1.0.0 (2026-01-19)
- 首次发布
- 支持多种声音预设（女声、男声、童声等）
- 基于 FFmpeg 的快速音高调整
- 支持自定义音高参数
- 可被其他 skills 调用集成
- 支持批量处理

## 更多信息

详细文档请查看 [SKILL.md](SKILL.md)

## License

MIT
