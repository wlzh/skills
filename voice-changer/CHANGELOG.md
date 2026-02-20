# Changelog

## v1.6.0 - 2026-02-20

### ✨ 新功能
- **支持视频直接输入** - 现在可以直接处理 .mp4 等视频文件，无需手动提取音频
- **自动提取和合成视频音频** - 输入视频时自动提取音频 → 变声处理 → 合成回视频

### 🐛 Bug 修复
- **修复 pedalboard 不支持 .mp4 输出** - 自动转换为 WAV 格式处理后再合成视频
- **修复 video-voice-changer 兼容性问题** - voice-changer 现在支持视频处理

### 🔧 技术改进
- 新增 `is_video_file()` 函数检测视频文件
- 新增 `extract_audio_from_video()` 提取视频音频
- 新增 `combine_audio_with_video()` 合成音频回视频

### 📝 使用方式

```bash
# 直接处理视频
python3 voice_change.py input.mp4 -v female_3 -o output.mp4

# 处理音频（原有功能）
python3 voice_change.py input.wav -v male_normal -o output.wav
```

---

## v1.5.0 - 2026-01-22

### 🐛 Bug 修复
- **修复长音频分块处理重复问题** - 合并时正确去除 2 秒重叠部分
- **修复默认声音读取** - 现在从配置文件读取 `default_voice` 而非硬编码

### ✨ 新功能
- **长音频自动分块处理** - 超过 60 秒自动使用分块处理，避免内存问题
- **Python 3.10 环境支持** - 新增 `rvc_env_310` 避免 fairseq 兼容性问题
- **智能 MP3 转换** - RVC 输出 40000Hz 自动重采样到 48000Hz

### 🔧 改进
- **RVC 不降级** - 强制使用 RVC，失败则返回错误（符合用户要求）
- **更好的日志输出** - 显示分块处理进度和合并状态
- **清理未使用代码** - 删除 `rvc_infer_standalone.py`

### 📝 已知问题
- Index 文件暂时禁用以节省内存
- CPU 模式处理较慢，建议使用 GPU

---

## v1.4.0 - 2026-01-21

### ✨ 新功能
- **完整 RVC Pipeline 实现** - 使用真实的 RVC 模型进行声音转换
- **HuBERT 模型集成** - 用于提取语音特征
- **Kohane 女声模型** - Project Sekai 日式女声模型
- **分块处理支持** - `rvc_process_long.py` 处理长音频

### 🔧 技术改进
- Python 3.10 环境 (rvc_env_310) 支持
- FAISS index 支持
- F0 提取方法 (harvest/crepe)

---

## v1.0.0 - 2026-01-19

### 🎉 首次发布

**音频变声处理工具** - 将音频转换为不同的声音效果

### ✨ 核心功能

- ✅ **多种声音预设** - 支持女声、男声、童声等多种预设
- ✅ **快速处理** - 基于 FFmpeg 的简单音高调整
- ✅ **Pedalboard 集成** - 高质量音频处理
- ✅ **灵活配置** - 支持自定义音高参数和配置文件
- ✅ **可集成** - 可被其他 skills 调用集成

### 🎵 声音预设

| 预设 | 音高 | 描述 |
|-----|------|------|
| female_1 | 0 | 女声（轻柔）RVC |
| female_2 | +2 | 女声（明亮）RVC |
| female_3 | -1 | 女声（甜美）RVC ⭐ 默认 |
| child | +8 | 童声 RVC |
| rvc_female | +4 | AI 女声（高音高） |
| rvc_male | -12 | AI 男声（低音高） |

### 📊 性能指标

- **短音频（<60秒）**: 直接 RVC 处理
- **长音频（>60秒）**: 自动分块处理（30秒/段，2秒重叠）
- **CPU 模式**: ~10-30秒/分钟
- **内存占用**: ~500MB

### 📦 命令行参数

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

### 📝 配置文件

默认配置文件: `config/voice_config.json`

### 🔮 未来计划

- [ ] 启用 Index 文件以提升音质
- [ ] GPU 加速支持
- [ ] 实时变声处理
- [ ] 更多 RVC 模型支持

### 📄 许可

MIT
