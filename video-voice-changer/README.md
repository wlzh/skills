# video-voice-changer

> 版本: v1.0.0

视频变声处理工具 - 对视频中的音频进行变声处理

## 快速开始

```bash
# 基本用法（转换为女声，覆盖原视频）
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py input.mp4

# 指定声音类型
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py input.mp4 -v male_deep

# 指定输出文件（不覆盖原视频）
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py input.mp4 -o output.mp4
```

## 功能特性

- 视频音频变声处理
- 复用 voice-changer skill 配置
- 保持原视频质量
- 临时文件自动清理
- 支持多种声音预设

## 依赖要求

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

## 声音预设

| 预设 | 音高 | 描述 |
|-----|------|------|
| female_1 | +1 | 女声（轻柔） |
| female_2 | +7 | 女声（明亮） |
| female_3 | +1 | 女声（甜美） |
| male_deep | -5 | 男声（低沉） |
| male_normal | -3 | 男声（正常） |
| child | +8 | 童声 |

## 命令行参数

```
usage: video_voice_change.py [-h] [-v VOICE] [-o OUTPUT] [-c CONFIG]
                             [--keep-audio] [--temp-dir TEMP_DIR]
                             input_video

参数:
  input_video           输入视频文件
  -v, --voice          声音类型（默认: female_1）
  -o, --output         输出文件路径（默认: 覆盖原视频）
  -c, --config         voice-changer 配置文件路径
  --keep-audio         保留提取的原始音频文件
  --temp-dir           自定义临时目录
```

## 使用示例

### 示例 1: 基本变声
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  video.mp4
```

### 示例 2: 指定声音并输出新文件
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  video.mp4 \
  -v male_deep \
  -o video_male.mp4
```

### 示例 3: 保留原始音频
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  video.mp4 \
  --keep-audio
```

## 处理流程

1. 从视频中提取音频（MP3 格式）
2. 调用 voice-changer skill 进行变声
3. 将变声后的音频与原视频合并
4. 清理临时文件

## 性能参考

- 10 分钟 1080p 视频: ~30-60 秒处理时间
- 内存占用: < 200MB
- CPU 占用: 中等到高

## 注意事项

1. 默认会覆盖原视频，建议先用 `-o` 参数测试
2. 视频编码保持不变，只替换音频
3. 处理大文件需要足够的磁盘空间
4. 音频编码为 AAC 格式

## 故障排除

**问题: 处理失败**
- 检查 FFmpeg 是否正确安装
- 确认 voice-changer skill 存在

**问题: 音视频不同步**
- 确保原视频文件完整
- 检查磁盘空间是否充足

## 更新记录

### v1.0.0 (2026-01-21)
- 首次发布
- 支持视频音频变声
- 复用 voice-changer 配置
- 保持原视频质量

## License

MIT
