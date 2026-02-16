---
name: audiocut-keyword
description: 音频关键字过滤工具 - 根据关键字配置自动识别并删除音频中的指定内容
version: 1.1.0
author: M.
---

# 音频关键字过滤工具

> 基于 FunASR 语音识别和 FFmpeg 剪辑的音频关键字过滤 Skill

## 功能特性

- **精确转录**: 使用 FunASR Paraformer 进行 30s 分段转录，获取字符级时间戳
- **关键字识别**: 根据配置文件自动识别音频中的关键字
- **智能剪辑**: 使用 FFmpeg 精确删除关键字片段并合成最终音频
- **可配置**: 支持自定义关键字列表和缓冲时间

## 使用场景

1. **YouTube 转播客**: 删除视频中的"关注"、"订阅"、"点赞"等引导语
2. **广告过滤**: 自动删除音频中的广告和推广内容
3. **内容清理**: 批量处理音频，删除不需要的关键字片段

## 快速开始

### 基本用法

```bash
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py <音频文件>
```

### 指定输出文件

```bash
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py \
  input.mp3 \
  -o output.mp3
```

### 使用自定义关键字配置

```bash
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py \
  input.mp3 \
  -k my_keywords.json
```

### 调整缓冲时间

```bash
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py \
  input.mp3 \
  --buffer-before 1.0 \
  --buffer-after 1.0
```

## 工作流程

```
1. 音频转录（FunASR 30s 分段）
   ↓
2. 加载关键字配置
   ↓
3. 查找关键字位置（字符级时间戳）
   ↓
4. 生成删除计划（合并重叠片段）
   ↓
5. FFmpeg 剪辑并合成
   ↓
6. 输出处理后的音频
```

## 关键字配置文件

配置文件位于: `~/.claude/skills/audiocut-keyword/config/keywords.json`

```json
{
  "keywords": [
    "广告",
    "赞助",
    "推广",
    "关注",
    "订阅",
    "点赞",
    "转发",
    "分享",
    "评论区",
    "链接在简介",
    "微信公众号",
    "小程序"
  ],
  "buffer_before": 0.5,
  "buffer_after": 0.5,
  "description": "关键字配置文件"
}
```

### 配置说明

- `keywords`: 关键字列表，支持中文和英文
- `buffer_before`: 删除前缓冲时间（秒），避免删除不完整
- `buffer_after`: 删除后缓冲时间（秒），避免删除不完整

## 技术实现

### 1. 音频转录

使用 FunASR Paraformer 模型进行 30s 分段转录：

- **模型**: `paraformer-zh` (中文语音识别)
- **分段策略**: 30s 一段，避免长音频时间戳漂移
- **时间戳精度**: 字符级（毫秒级）
- **输出格式**: JSON（包含每个字符的 start/end 时间戳）

### 2. 关键字识别

- 在转录文本中使用正则表达式查找关键字
- 根据字符位置获取对应的时间戳
- 记录上下文信息，便于审查

### 3. 删除计划生成

- 为每个关键字添加前后缓冲时间
- 合并重叠的时间段，避免重复删除
- 生成最终的删除片段列表

### 4. 音频剪辑

使用 FFmpeg filter_complex 进行无损剪辑：

```bash
ffmpeg -i input.mp3 \
  -filter_complex "[0:a]atrim=start=0:end=10,asetpts=PTS-STARTPTS[a0];
                   [0:a]atrim=start=15:end=30,asetpts=PTS-STARTPTS[a1];
                   [a0][a1]concat=n=2:v=0:a=1[outa]" \
  -map "[outa]" output.mp3
```

## 输出文件

处理完成后会生成以下文件：

- `<原文件名>_filtered.mp3` - 处理后的音频
- `<原文件名>_delete_plan.json` - 删除计划（包含匹配信息）
- `<原文件名>_transcript.json` - 转录文件（可选保留）

## 命令行参数

```
usage: audiocut_keyword.py [-h] [-o OUTPUT] [-k KEYWORDS]
                           [--buffer-before BUFFER_BEFORE]
                           [--buffer-after BUFFER_AFTER]
                           [--keep-transcript]
                           input_audio

positional arguments:
  input_audio           输入音频文件

optional arguments:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出音频文件（默认：输入文件名_filtered.mp3）
  -k KEYWORDS, --keywords KEYWORDS
                        关键字配置文件（默认：config/keywords.json）
  --buffer-before BUFFER_BEFORE
                        删除前缓冲时间（秒，默认：0.5）
  --buffer-after BUFFER_AFTER
                        删除后缓冲时间（秒，默认：0.5）
  --keep-transcript     保留转录文件
```

## 依赖安装

### FunASR 环境（推荐）

使用预配置的 Python 3.10 环境：

```bash
# FunASR 环境已预安装在 skill 目录
~/.claude/skills/audiocut-keyword/funasr_env_310/
```

包含：
- Python 3.10
- torch 2.10.0
- funasr 1.3.0

### 手动安装 Python 依赖

```bash
pip install funasr modelscope
```

### 系统依赖

- FFmpeg (用于音频处理)
- ffprobe (用于获取音频信息)

### 模型下载

首次运行会自动下载 FunASR 模型（约 2GB）到 `~/.cache/modelscope/`

## 性能参考

| 指标 | 值 |
|------|-----|
| 转录速度 | ~0.16x 实时（1分钟音频约10秒处理） |
| 剪辑速度 | 几乎瞬时完成 |
| 15分钟音频 | 总处理时间约 2-3 分钟 |

*测试环境：M1 Mac，CPU 推理*

## 集成到 youtube-to-xiaoyuzhou

在 youtube-to-xiaoyuzhou 工作流中使用：

```python
# 下载 YouTube 音频后
audio_file = "downloaded_audio.mp3"

# 过滤关键字
filtered_audio = audiocut_keyword(audio_file)

# 上传到小宇宙
upload_to_xiaoyuzhou(filtered_audio)
```

## 注意事项

1. **首次运行**: 需要下载 FunASR 模型，可能需要几分钟
2. **音频格式**: 支持 MP3, WAV, M4A 等常见格式
3. **关键字匹配**: 精确匹配，不支持模糊匹配
4. **缓冲时间**: 建议设置 0.5-1.0 秒，避免删除不完整
5. **长音频**: 30s 分段策略确保时间戳精确，无长度限制

## 常见问题

### Q1: 转录准确率低

**原因**: 背景噪音大、口音重、音质差

**解决**:
- 使用降噪工具预处理音频
- 调整音频采样率为 16kHz
- 检查音频是否清晰

### Q2: 关键字未被识别

**原因**: 转录错误或关键字配置不准确

**解决**:
- 检查转录文件 `*_transcript.json` 中的文本
- 调整关键字配置，使用转录中的实际文本
- 添加关键字的变体（如"关注"、"关注一下"）

### Q3: 删除了不该删除的内容

**原因**: 关键字过于宽泛或缓冲时间过长

**解决**:
- 使用更具体的关键字
- 减小缓冲时间
- 检查删除计划文件 `*_delete_plan.json`

### Q4: FFmpeg 执行失败

**原因**: FFmpeg 未安装或版本过旧

**解决**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# 检查版本
ffmpeg -version
```

## 示例

### 示例 1: 处理 YouTube 音频

```bash
# 下载 YouTube 音频
yt-dlp -x --audio-format mp3 https://youtu.be/xxxxx -o input.mp3

# 过滤关键字
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py input.mp3

# 输出: input_filtered.mp3
```

### 示例 2: 自定义关键字

创建 `my_keywords.json`:
```json
{
  "keywords": ["广告", "赞助商", "推广链接"],
  "buffer_before": 1.0,
  "buffer_after": 1.0
}
```

运行:
```bash
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py \
  input.mp3 \
  -k my_keywords.json
```

### 示例 3: 批量处理

```bash
for file in *.mp3; do
  python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py "$file"
done
```

## 未来扩展

- [ ] 支持模糊匹配和正则表达式
- [ ] 支持多语言（英文、日文等）
- [ ] 添加 GUI 界面
- [ ] 支持实时预览删除效果
- [ ] 集成到更多播客工作流

## License

MIT
