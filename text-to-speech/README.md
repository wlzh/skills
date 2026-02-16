# text-to-speech

> 版本: v1.0.0

文本转语音工具 - 支持播客脚本解析、情绪标记和后处理

## 快速开始

```bash
# 基本用法
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py <文本文件>

# 指定输出文件
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -o output.mp3

# 使用女声
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -v zh-CN-XiaoxiaoNeural
```

## 功能特性

- 🎤 **高质量 TTS** - 基于 Microsoft Edge TTS，支持 18+ 种中文声音
- 📝 **脚本解析** - 自动识别并移除播客脚本中的注释和标记
- 🎭 **情绪标记** - 支持 SSML 情绪标记处理（可配置）
- 🎵 **后处理集成** - 可选集成 voice-changer 进行变声
- ⚙️ **高度可配置** - 所有功能都可通过配置文件控制

## 脚本解析能力

自动移除以下内容：
- `(00:00)` - 时间戳
- `[BGM渐入：...]` - 背景音乐注释
- `(主播声音：...)` - 导演指示
- `(停顿 1秒)` - 动作指示
- `(语速放慢，加重语气)` - 情绪标记
- `**文本**` - Markdown 加粗标记

只保留实际要朗读的文字。

## 支持的声音

### 男声
- `zh-CN-YunyangNeural` - 新闻播音（沉稳专业）⭐ 默认
- `zh-CN-YunxiNeural` - 年轻活力
- `zh-CN-YunjianNeural` - 成熟稳重
- `zh-CN-YunfengNeural` - 新闻播音
- `zh-CN-YunhaoNeural` - 广告配音
- `zh-CN-YunzeNeural` - 年轻阳光

### 女声
- `zh-CN-XiaoxiaoNeural` - 温柔亲切
- `zh-CN-XiaoyiNeural` - 活泼开朗
- `zh-CN-XiaochenNeural` - 知性优雅
- `zh-CN-XiaohanNeural` - 严肃正式
- `zh-CN-XiaomengNeural` - 少女可爱
- `zh-CN-XiaomoNeural` - 温暖治愈
- `zh-CN-XiaoqiuNeural` - 叙事讲述
- `zh-CN-XiaoruiNeural` - 平和自然
- `zh-CN-XiaoshuangNeural` - 儿童声音
- `zh-CN-XiaoxuanNeural` - 温柔细腻
- `zh-CN-XiaoyanNeural` - 新闻播音
- `zh-CN-XiaoyouNeural` - 儿童声音

## 命令行参数

```
usage: text_to_speech.py [-h] [-o OUTPUT] [-c CONFIG] [-v VOICE]
                         [--rate RATE] [--pitch PITCH] [--volume VOLUME]
                         [--post-process] [--list-voices]
                         input

参数:
  input                 输入文本文件路径（或使用 - 从标准输入读取）
  -o, --output         输出音频文件路径
  -c, --config         配置文件路径
  -v, --voice          声音类型（如 zh-CN-YunyangNeural）
  --rate               语速调整（如 +20% 或 -10%）
  --pitch              音调调整（如 +5Hz 或 -3Hz）
  --volume             音量调整（如 +20% 或 -10%）
  --post-process       启用后处理（voice-changer）
  --list-voices        列出所有可用的声音
```

## 使用示例

### 示例 1: 转换播客脚本

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py podcast_script.txt
```

输入脚本：
```
(00:00) [BGM渐入：深沉的电子低音]
(主播声音：稳重，中速)
大家好，这里是AI前沿播客。
(停顿 1秒)
今天我们要聊的话题，关乎一场正在发生的剧变。
```

实际朗读：
```
大家好，这里是AI前沿播客。
今天我们要聊的话题，关乎一场正在发生的剧变。
```

### 示例 2: 使用女声并调整语速

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py \
  script.txt \
  -v zh-CN-XiaoxiaoNeural \
  --rate "+10%"
```

### 示例 3: 启用后处理

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py \
  script.txt \
  --post-process
```

会先生成语音，然后调用 voice-changer 进行变声处理。

### 示例 4: 从标准输入读取

```bash
echo "你好，世界！欢迎使用 Text-to-Speech。" | \
  python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py -
```

### 示例 5: 列出所有可用声音

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py --list-voices
```

## 配置文件

编辑 `config/tts_config.json` 自定义设置：

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
  "post_processing": {
    "enabled": false,
    "voice_changer": {
      "enabled": false,
      "voice_type": "female_1"
    }
  }
}
```

## 依赖安装

```bash
# 安装 Edge TTS
pip install edge-tts

# 验证安装
edge-tts --version
```

## 输出文件

- 默认输出位置：与输入文件相同目录
- 默认文件名：`<原文件名>_tts.mp3`
- 如果启用后处理：`<原文件名>_tts_voice_changed.mp3`

## 性能参考

- 1000 字文本：约 10-20 秒
- 5000 字文本：约 30-60 秒
- 10000 字文本：约 60-120 秒

*网络速度影响较大*

## 注意事项

1. **网络要求**：Edge TTS 需要网络连接
2. **文本长度**：建议单次转换不超过 10000 字
3. **脚本格式**：支持纯文本和带注释的播客脚本
4. **后处理**：需要先安装 voice-changer skill

## 故障排除

**问题: 网络连接失败**
- 检查网络连接
- 尝试使用代理

**问题: 声音不自然**
- 尝试调整语速和音调
- 更换不同的声音

**问题: 后处理失败**
- 确认 voice-changer skill 已安装
- 检查 voice-changer 配置

## 更新记录

### v1.0.0 (2026-01-20)
- 首次发布
- 支持 Edge TTS 语音合成
- 支持播客脚本解析
- 支持 18+ 种中文声音
- 支持语速、音调、音量调整
- 支持 voice-changer 后处理集成
- 高度可配置

## 详细文档

查看 [SKILL.md](SKILL.md) 获取完整文档。

## License

MIT
