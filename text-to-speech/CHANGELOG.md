# Changelog

## v1.0.0 - 2026-01-20

### 🎉 首次发布

**文本转语音工具** - 支持播客脚本解析、情绪标记和后处理

### ✨ 核心功能

- ✅ **Edge TTS 集成** - 基于 Microsoft Edge TTS，免费高质量
- ✅ **18+ 种中文声音** - 支持多种男声和女声，适合不同场景
- ✅ **脚本解析** - 自动识别并移除播客脚本中的注释和标记
- ✅ **情绪标记处理** - 支持 SSML 情绪标记（可配置）
- ✅ **后处理集成** - 可选集成 voice-changer 进行变声
- ✅ **高度可配置** - 所有功能都可通过配置文件控制

### 📝 脚本解析能力

自动移除以下内容：
- `(00:00)` - 时间戳
- `[BGM渐入：...]` - 背景音乐注释
- `(主播声音：...)` - 导演指示
- `(停顿 1秒)` - 动作指示
- `(语速放慢，加重语气)` - 情绪标记
- `**文本**` - Markdown 加粗标记

### 🎤 支持的声音

**男声**：
- zh-CN-YunyangNeural（新闻播音，沉稳专业）⭐ 默认
- zh-CN-YunxiNeural（年轻活力）
- zh-CN-YunjianNeural（成熟稳重）
- zh-CN-YunfengNeural（新闻播音）
- zh-CN-YunhaoNeural（广告配音）
- zh-CN-YunzeNeural（年轻阳光）

**女声**：
- zh-CN-XiaoxiaoNeural（温柔亲切）
- zh-CN-XiaoyiNeural（活泼开朗）
- zh-CN-XiaochenNeural（知性优雅）
- zh-CN-XiaohanNeural（严肃正式）
- zh-CN-XiaomengNeural（少女可爱）
- zh-CN-XiaomoNeural（温暖治愈）
- zh-CN-XiaoqiuNeural（叙事讲述）
- zh-CN-XiaoruiNeural（平和自然）
- zh-CN-XiaoshuangNeural（儿童声音）
- zh-CN-XiaoxuanNeural（温柔细腻）
- zh-CN-XiaoyanNeural（新闻播音）
- zh-CN-XiaoyouNeural（儿童声音）

### 🔧 技术实现

**TTS 引擎**：
- Microsoft Edge TTS（免费、高质量）
- 支持语速、音调、音量调整
- 支持 SSML 标记

**脚本解析**：
- 正则表达式匹配
- 可配置的解析规则
- 保留实际要朗读的文本

**后处理**：
- 可选集成 voice-changer skill
- 支持变声处理
- 可配置的后处理参数

### 📊 性能指标

- 1000 字文本：约 10-20 秒
- 5000 字文本：约 30-60 秒
- 10000 字文本：约 60-120 秒

*网络速度影响较大*

### 📦 命令行参数

```
usage: text_to_speech.py [-h] [-o OUTPUT] [-c CONFIG] [-v VOICE]
                         [--rate RATE] [--pitch PITCH] [--volume VOLUME]
                         [--post-process] [--list-voices]
                         input

参数:
  input                 输入文本文件路径
  -o, --output         输出音频文件路径
  -c, --config         配置文件路径
  -v, --voice          声音类型
  --rate               语速调整
  --pitch              音调调整
  --volume             音量调整
  --post-process       启用后处理
  --list-voices        列出所有可用声音
```

### 🎯 使用场景

1. **播客制作** - 将播客脚本转换为语音
2. **有声读物** - 将文章、小说转换为音频
3. **视频配音** - 为视频生成旁白
4. **语音助手** - 生成语音提示
5. **教育培训** - 制作教学音频

### 📚 依赖要求

**Python 依赖**：
- edge-tts

**可选依赖**：
- voice-changer skill（用于后处理）

### ⚙️ 配置文件

默认配置文件：`config/tts_config.json`

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

### 🔮 未来计划

- [ ] 支持更多语言（英文、日文等）
- [ ] 支持批量处理
- [ ] 支持更高级的 SSML 标记
- [ ] 支持背景音乐混合
- [ ] 添加 GUI 界面
- [ ] 支持实时语音合成

### 📄 许可

MIT
