# video-voice-changer Skill 测试指南

## 测试日期
2026-01-21

## 一、环境准备

### 1.1 检查依赖

```bash
# 检查 FFmpeg
ffmpeg -version
ffprobe -version

# 检查 Python
python3 --version

# 检查 voice-changer skill
ls ~/.claude/skills/voice-changer/scripts/voice_change.py
```

### 1.2 准备测试视频

准备一个短视频文件（建议 30 秒 - 2 分钟）用于测试：

```bash
# 下载测试视频或使用你自己的视频
# 保存为 test_video.mp4
```

## 二、基础功能测试

### 2.1 测试 1: 基本变声（默认女声）

**目的**: 验证基本的视频变声功能

**步骤**:
```bash
# 使用测试视频（会覆盖原视频，建议先复制）
cp test_video.mp4 test_video_backup.mp4

python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4
```

**预期结果**:
- 视频被处理
- 音调提高（女声效果）
- 视频画质保持不变
- 时长保持不变

**验证**:
```bash
# 播放验证
open test_video.mp4  # macOS
# 或
vlc test_video.mp4   # Linux
```

### 2.2 测试 2: 指定声音类型

**目的**: 验证不同声音预设

**步骤**:
```bash
# 测试男声（低沉）
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v male_deep \
  -o test_video_male.mp4

# 测试童声
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v child \
  -o test_video_child.mp4
```

**预期结果**:
- male_deep: 音调降低
- child: 音调显著提高

### 2.3 测试 3: 输出到新文件

**目的**: 验证不覆盖原视频

**步骤**:
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -o test_video_output.mp4
```

**预期结果**:
- 生成 `test_video_output.mp4`
- 原视频 `test_video.mp4` 保持不变

### 2.4 测试 4: 保留原始音频

**目的**: 验证保留音频功能

**步骤**:
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  --keep-audio
```

**预期结果**:
- 视频被处理
- 生成 `test_video_voice_changed.mp3`（原始音频）

### 2.5 测试 5: 查看帮助信息

**步骤**:
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py --help
```

**预期结果**:
显示完整的帮助信息

## 三、集成测试

### 3.1 测试 6: 与 voice-changer 配置联动

**目的**: 验证使用 voice-changer 的配置

**步骤**:
```bash
# 编辑 voice-changer 配置
# 添加新的声音预设
vim ~/.claude/skills/voice-changer/config/voice_config.json

# 使用新预设
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v custom_voice
```

## 四、性能测试

### 4.1 测试 7: 短视频处理速度

**视频**: 30 秒 - 1 分钟

**步骤**:
```bash
time python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  short_video.mp4
```

**预期结果**:
- 处理时间: < 30 秒
- 内存占用: < 200MB

### 4.2 测试 8: 长视频处理速度

**视频**: 10 分钟+

**步骤**:
```bash
time python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  long_video.mp4
```

**预期结果**:
- 处理时间: 30-60 秒
- 无崩溃或超时

## 五、错误处理测试

### 5.1 测试 9: 不存在的文件

**步骤**:
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  nonexistent.mp4
```

**预期结果**:
- 显示错误信息
- 退出码: 1

### 5.2 测试 10: 无效的声音类型

**步骤**:
```bash
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v invalid_voice
```

**预期结果**:
- voice-changer 会显示警告并使用默认配置

### 5.3 测试 11: 无效的视频格式

**步骤**:
```bash
# 使用非视频文件
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test.txt
```

**预期结果**:
- FFmpeg 返回错误
- 显示错误信息

## 六、视频格式兼容性测试

### 6.1 测试 12: 不同视频格式

**步骤**:
```bash
# MP4
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py test.mp4 -o out.mp4

# MOV
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py test.mov -o out.mov

# MKV
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py test.mkv -o out.mkv
```

**预期结果**:
- 常见格式都能正常处理

## 七、测试记录表

| 测试编号 | 测试项 | 状态 | 备注 |
|---------|--------|------|------|
| 1 | 基本变声 | ⬜ 待测试 | |
| 2 | 指定声音类型 | ⬜ 待测试 | |
| 3 | 输出到新文件 | ⬜ 待测试 | |
| 4 | 保留原始音频 | ⬜ 待测试 | |
| 5 | 帮助信息 | ⬜ 待测试 | |
| 6 | voice-changer 配置联动 | ⬜ 待测试 | |
| 7 | 短视频性能 | ⬜ 待测试 | |
| 8 | 长视频性能 | ⬜ 待测试 | |
| 9 | 错误处理 - 不存在文件 | ⬜ 待测试 | |
| 10 | 错误处理 - 无效声音 | ⬜ 待测试 | |
| 11 | 错误处理 - 无效格式 | ⬜ 待测试 | |
| 12 | 视频格式兼容性 | ⬜ 待测试 | |

## 八、快速测试命令

```bash
# 准备测试文件
cp your_test_video.mp4 test_video.mp4

# 基础测试
python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -o test_female.mp4

python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v male_deep \
  -o test_male.mp4

python3 ~/.claude/skills/video-voice-changer/scripts/video_voice_change.py \
  test_video.mp4 \
  -v child \
  -o test_child.mp4

# 播放测试结果
open test_female.mp4
open test_male.mp4
open test_child.mp4

echo "测试完成！请播放视频验证效果"
```

## 九、已知问题和限制

### 9.1 当前限制

1. **处理时间**: 与视频长度成正比
2. **磁盘空间**: 需要临时空间存储音频文件
3. **音质**: 继承 voice-changer 的音质特性

### 9.2 改进建议

1. 添加进度条显示
2. 支持批量处理
3. 添加音视频同步检测
4. 支持更多输出格式
