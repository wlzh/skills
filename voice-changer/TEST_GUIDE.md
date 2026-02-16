# voice-changer Skill 测试指南

## 测试日期
2026-01-19

## 一、环境准备

### 1.1 检查依赖

运行测试脚本检查环境：

```bash
bash ~/.claude/skills/voice-changer/test_voice_changer.sh
```

预期输出：
- ✅ Python3 已安装
- ✅ FFmpeg 已安装
- ✅ FFprobe 已安装
- ✅ voice_change.py 语法正确
- ✅ voice_config.json 格式有效

### 1.2 安装缺失依赖

如果 FFmpeg 未安装：

```bash
bash ~/.claude/skills/voice-changer/install_dependencies.sh
```

## 二、基础功能测试

### 2.1 测试 1: 基本变声（默认女声）

**目的**: 验证基本的变声功能

**步骤**:
```bash
# 使用你的测试音频文件
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  /path/to/test_audio.mp3
```

**预期结果**:
- 生成 `test_audio_voice_changed.mp3`
- 音调提高约 5 个半音
- 文件大小相近
- 音频时长不变

**验证**:
```bash
# 检查输出文件
ls -lh test_audio_voice_changed.mp3

# 播放验证
open test_audio_voice_changed.mp3  # macOS
# 或
vlc test_audio_voice_changed.mp3   # Linux
```

### 2.2 测试 2: 指定声音类型

**目的**: 验证不同声音预设

**步骤**:
```bash
# 测试女声 2（更高音调）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  test_audio.mp3 \
  -v female_2

# 测试男声（低沉）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  test_audio.mp3 \
  -v male_deep
```

**预期结果**:
- female_2: 音调更高（+7 半音）
- male_deep: 音调降低（-5 半音）

### 2.3 测试 3: 自定义音高

**目的**: 验证自定义音高参数

**步骤**:
```bash
# 自定义提高 6 个半音
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  test_audio.mp3 \
  -p 6 \
  -o custom_voice.mp3
```

**预期结果**:
- 生成 `custom_voice.mp3`
- 音高按指定值调整

### 2.4 测试 4: 查看帮助信息

**步骤**:
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py --help
```

**预期结果**:
显示完整的帮助信息，包括所有参数说明

## 三、集成测试

### 3.1 测试 5: 与 audiocut-keyword 集成

**目的**: 验证在关键字过滤后进行变声

**步骤**:
```bash
# 先过滤关键字，再变声
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py \
  test_audio.mp3 \
  --change-voice female_1
```

**预期结果**:
- 生成 `test_audio_filtered.mp3`（过滤后）
- 生成 `test_audio_filtered_voice_changed.mp3`（变声后）
- 两个步骤都成功完成

### 3.2 测试 6: 与 youtube-to-xiaoyuzhou 集成

**目的**: 验证完整工作流

**步骤**:
```bash
# YouTube 下载 + 过滤 + 变声（预览模式）
python3 ~/.claude/skills/youtube-to-xiaoyuzhou/youtube_to_xiaoyuzhou.py \
  https://youtu.be/xxxxx \
  --filter-keywords \
  --change-voice female_1 \
  --preview
```

**预期结果**:
- 下载音频成功
- 过滤关键字成功
- 变声处理成功
- 预览模式显示所有信息

## 四、性能测试

### 4.1 测试 7: 短音频处理速度

**音频**: 1 分钟

**步骤**:
```bash
time python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  short_audio.mp3
```

**预期结果**:
- 处理时间: < 5 秒
- 内存占用: < 100MB

### 4.2 测试 8: 长音频处理速度

**音频**: 14 分钟（如 "AI 重塑数学研究.mp3"）

**步骤**:
```bash
time python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  long_audio.mp3 \
  -v female_1
```

**预期结果**:
- 处理时间: 7-14 秒
- 内存占用: < 200MB
- 无崩溃或超时

## 五、错误处理测试

### 5.1 测试 9: 不存在的文件

**步骤**:
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  nonexistent.mp3
```

**预期结果**:
- 显示错误信息: "输入文件不存在"
- 退出码: 1

### 5.2 测试 10: 无效的声音类型

**步骤**:
```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  test_audio.mp3 \
  -v invalid_voice
```

**预期结果**:
- 显示警告: "未找到声音配置"
- 使用默认配置继续处理

### 5.3 测试 11: 无效的音高值

**步骤**:
```bash
# 超出合理范围
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  test_audio.mp3 \
  -p 20
```

**预期结果**:
- 处理完成但音质可能较差
- 显示警告（如果实现了范围检查）

## 六、音质评估

### 6.1 主观评估标准

对每个测试输出进行主观评估：

| 评估项 | 标准 |
|--------|------|
| 清晰度 | 语音是否清晰可辨 |
| 自然度 | 声音是否自然 |
| 失真度 | 是否有明显失真 |
| 可用性 | 是否适合实际使用 |

### 6.2 推荐音高范围

基于测试结果：

- **女声**: +3 到 +7 半音（推荐 +5）
- **男声**: -3 到 -7 半音（推荐 -5）
- **童声**: +6 到 +10 半音（推荐 +8）

## 七、测试记录表

| 测试编号 | 测试项 | 状态 | 备注 |
|---------|--------|------|------|
| 1 | 基本变声 | ⬜ 待测试 | |
| 2 | 指定声音类型 | ⬜ 待测试 | |
| 3 | 自定义音高 | ⬜ 待测试 | |
| 4 | 帮助信息 | ⬜ 待测试 | |
| 5 | audiocut-keyword 集成 | ⬜ 待测试 | |
| 6 | youtube-to-xiaoyuzhou 集成 | ⬜ 待测试 | |
| 7 | 短音频性能 | ⬜ 待测试 | |
| 8 | 长音频性能 | ⬜ 待测试 | |
| 9 | 错误处理 - 不存在文件 | ⬜ 待测试 | |
| 10 | 错误处理 - 无效声音 | ⬜ 待测试 | |
| 11 | 错误处理 - 无效音高 | ⬜ 待测试 | |

## 八、已知问题和限制

### 8.1 当前限制

1. **音质损失**: 音高调整会带来一定的音质损失
2. **处理速度**: 长音频处理需要一定时间
3. **效果局限**: Simple 方法效果不如 AI 模型

### 8.2 改进建议

1. 集成 RVC 模型以获得更好的音质
2. 添加批量处理功能
3. 添加进度显示
4. 支持更多音效（回声、混响等）

## 九、测试结论模板

测试完成后填写：

```
测试日期: ____________________
测试人员: ____________________

通过的测试: ____ / 11
失败的测试: ____

总体评价:
□ 优秀 - 所有测试通过，音质良好
□ 良好 - 大部分测试通过，可用于生产
□ 一般 - 部分测试失败，需要改进
□ 较差 - 多数测试失败，不建议使用

主要问题:
1. ____________________
2. ____________________

建议:
1. ____________________
2. ____________________
```

## 十、快速测试命令

```bash
# 一键运行所有基础测试
cd ~/.claude/skills/voice-changer

# 1. 环境检查
bash test_voice_changer.sh

# 2. 基本功能测试（需要准备 test.mp3）
python3 scripts/voice_change.py test.mp3
python3 scripts/voice_change.py test.mp3 -v female_2
python3 scripts/voice_change.py test.mp3 -v male_deep
python3 scripts/voice_change.py test.mp3 -p 6

# 3. 错误处理测试
python3 scripts/voice_change.py nonexistent.mp3
python3 scripts/voice_change.py test.mp3 -v invalid

echo "测试完成！请检查生成的音频文件"
```
