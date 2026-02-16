# voice-changer

> 版本: v1.5.0

音频变声处理工具 - 使用 RVC AI 模型进行真实的声音转换

## 特性

- 🎙️ **RVC AI 模型** - 真实的音色转换（不只是音高调整）
- ⚡ **自动分块处理** - 长音频自动分块，避免内存问题
- 🔧 **灵活配置** - 支持多种声音预设和自定义参数
- 🔌 **可被调用** - 可被其他 skills 集成调用

## 快速开始

```bash
# 基本用法（使用配置文件默认声音）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3

# 指定声音类型
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -v rvc_female

# 查看所有可用声音
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 --help
```

## 声音预设

### RVC AI 声音（当前默认方法）

| 预设 | 音高 | 描述 |
|-----|------|------|
| female_1 | 0 | 女声（轻柔） ⭐ |
| female_2 | +2 | 女声（明亮） |
| female_3 | -1 | 女声（甜美）⭐ **默认** |
| child | +8 | 童声 |
| rvc_female | +4 | AI 女声（高音高） |
| rvc_male | -12 | AI 男声（低音高） |
| male_normal | -8 | 男声（正常） |
| male_deep | -12 | 男声（低沉） |

> **注意**: RVC 方法可以真正转换音色，模型使用 Kohane (Project Sekai 日式女声)

### 模型资源

更多 RVC 变声器模型可参考：
- **260款RVC变声器模型**: https://pan.quark.cn/s/1cf1c5d6d4a6

## 命令行参数

```
usage: voice_change.py [-h] [-o OUTPUT] [-v VOICE] [-c CONFIG]
                       [-m {simple,pedalboard,rvc}] [-p PITCH] input_audio

参数:
  input_audio           输入音频文件
  -o, --output         输出文件路径
  -v, --voice          声音类型（默认: 从配置文件读取 default_voice）
  -c, --config         自定义配置文件
  -m, --method         处理方法: simple, pedalboard, 或 rvc
  -p, --pitch          音高调整（半音，覆盖配置）
```

## 使用示例

### 示例 1: 使用默认声音
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  input.mp3
```

### 示例 2: 指定 AI 女声
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  input.mp3 -v rvc_female
```

### 示例 3: 自定义音高
```bash
# 提高 6 个半音
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  input.mp3 -p 6
```

### 示例 4: 批量处理
```bash
for file in *.mp3; do
  python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
    "$file" -v female_3
done
```

## 技术实现

### RVC Pipeline 流程

```
输入音频 → 分块(如果>60秒) → HuBERT 特征提取 → F0 提取 → RVC 模型推理 → 合并 → MP3 转换
```

1. **分块处理**: 长音频自动分割成 30 秒段（2 秒重叠）
2. **HuBERT**: 提取语音表示特征
3. **F0 提取**: 使用 harvest 方法提取基频
4. **RVC 推理**: 使用 Kohane 模型进行声音转换
5. **智能合并**: 去除重叠部分，避免重复
6. **MP3 转换**: 40000Hz 自动重采样到 48000Hz

## 性能参考

| 音频时长 | 处理方式 | 处理时间 |
|---------|---------|---------|
| < 60秒 | 直接 RVC | ~10-30 秒 |
| > 60秒 | 分块 RVC | ~3-5 分钟（15分钟音频） |
| 875秒 | 分块 RVC | ~15 分钟（32 段） |

**测试环境**: Apple Silicon M1, CPU 模式

## 环境要求

### 系统依赖

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### Python 环境

RVC 需要 Python 3.10 环境（避免 fairseq 兼容性问题）：

```bash
# 已包含在 skill 中
~/.claude/skills/voice-changer/models/rvc_env_310/
```

已安装依赖：
- torch==2.5.1
- fairseq==0.12.2
- librosa
- soundfile
- pyworld
- parselmouth
- faiss-cpu
- torchcrepe
- pedalboard

## 配置文件

编辑 `config/voice_config.json`:

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

## 集成到其他 Skills

### Python 调用

```python
import subprocess
import os

def change_voice(input_audio, voice_type='female_3'):
    script = os.path.expanduser(
        '~/.claude/skills/voice-changer/scripts/voice_change.py'
    )
    output = input_audio.replace('.mp3', '_changed.mp3')

    cmd = ['python3', script, input_audio, '-v', voice_type, '-o', output]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return output if result.returncode == 0 else input_audio
```

### Bash 调用

```bash
#!/bin/bash
VOICE_CHANGER="$HOME/.claude/skills/voice-changer/scripts/voice_change.py"

# 变声处理
python3 "$VOICE_CHANGER" input.mp3 -v female_3
```

## 故障排除

### 问题: 处理速度慢
- CPU 模式处理较慢是正常的
- 如有 GPU 可修改 `rvc_infer_real.py` 使用 CUDA

### 问题: 内存不足
- 已自动分块处理，长音频不会 OOM
- 如仍有问题，可减小分块大小（修改 `chunk_duration`）

### 问题: 音质不佳
- 确保使用高质量输入音频
- 暂时禁用了 index 文件以节省内存
- 可在配置中启用 `index_path`

## 更新记录

### v1.5.0 (2026-01-22)
- 修复长音频分块处理重复问题
- 修复默认声音读取
- 新增长音频自动分块处理
- 新增 Python 3.10 环境支持

### v1.4.0 (2026-01-21)
- 集成 RVC AI 模型支持
- 添加 Kohane 女声模型
- 新增 HuBERT 特征提取

### v1.0.0 (2026-01-19)
- 首次发布

## 更多信息

- [SKILL.md](SKILL.md) - Skill 详细文档
- [CHANGELOG.md](CHANGELOG.md) - 更新日志
- [models/RVC_MODEL_GUIDE.md](models/RVC_MODEL_GUIDE.md) - RVC 模型指南

## License

MIT
