# text-to-speech

> 仓库地址: https://github.com/wlzh/skills
> 版本: v3.3.1

文本转语音工具 - 默认 MiniMax TTS，支持切换 Kokoro TTS 和 Edge TTS，保留播客脚本解析、情绪标记和后处理。

## 快速开始

```bash
# 基本用法
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py <文本文件>

# 设置 MiniMax API Key（只在本机环境变量中设置，不写入配置文件）
export MINIMAX_API_KEY="你的本机 key"

# 指定输出文件
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -o output.mp3

# 切换回 Kokoro 或 Edge
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --engine kokoro
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --engine edge
```

## 功能特性

- 🎤 **默认 MiniMax TTS** - 默认音色 `Chinese (Mandarin)_Reliable_Executive`（可靠高管）
- 🗣️ **MiniMax 语境适配** - 自动按开场、解释、步骤、提醒、总结、关注引导等语境轻量调整表达
- 🔁 **多引擎切换** - `tts_engine` 可配置为 `minimax`、`kokoro` 或 `edge`
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

### MiniMax
- `Chinese (Mandarin)_Reliable_Executive` - 可靠高管，男声，稳重可信，当前默认
- `Chinese (Mandarin)_Sincere_Adult` - 真诚成年，男声，自然真诚
- `Chinese (Mandarin)_Radio_Host` - 电台主持，男声，自然主持感
- `Chinese (Mandarin)_Gentle_Youth` - 温柔青年，男声，年轻柔和
- `Chinese (Mandarin)_Unrestrained_Young_Man` - 不羁青年，男声，轻松活跃
- `male-qn-jingying` - 精英青年，男声，清晰专业，旧默认

### Edge 男声
- `zh-CN-YunyangNeural` - 新闻播音（沉稳专业）⭐ 默认
- `zh-CN-YunxiNeural` - 年轻活力
- `zh-CN-YunjianNeural` - 成熟稳重
- `zh-CN-YunfengNeural` - 新闻播音
- `zh-CN-YunhaoNeural` - 广告配音
- `zh-CN-YunzeNeural` - 年轻阳光

### Edge 女声
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
                         [--engine {minimax,edge,kokoro}]
                         [--rate RATE] [--pitch PITCH] [--volume VOLUME]
                         [--speed SPEED] [--context CONTEXT]
                         [--post-process] [--list-voices]
                         input

参数:
  input                 输入文本文件路径（或使用 - 从标准输入读取）
  -o, --output         输出音频文件路径
  -c, --config         配置文件路径
  -e, --engine         TTS 引擎（minimax / kokoro / edge）
  -v, --voice          声音类型（如 zh-CN-YunyangNeural）
  --rate               语速调整（Edge，如 +20% 或 -10%）
  --pitch              音调调整（Edge 或 MiniMax）
  --volume             音量调整（Edge 或 MiniMax）
  --speed              语速（MiniMax/Kokoro，如 1.0）
  --context            MiniMax 专属语境档；默认自动识别，Edge/Kokoro 忽略
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

### 示例 2: 使用默认 MiniMax 音色并调整语速

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py \
  script.txt \
  -o output.mp3 \
  --speed 1.0
```

### 示例 3: 切回 Edge 女声

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py \
  script.txt \
  --engine edge \
  -v zh-CN-XiaoxiaoNeural \
  --rate "+10%"
```

### 示例 4: 启用后处理

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py \
  script.txt \
  --post-process
```

会先生成语音，然后调用 voice-changer 进行变声处理。

### 示例 5: 从标准输入读取

```bash
echo "你好，世界！欢迎使用 Text-to-Speech。" | \
  python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py -
```

### 示例 6: 列出所有可用声音

```bash
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py --list-voices
```

## 配置文件

编辑 `config/tts_config.json` 自定义设置：

```json
{
  "tts_engine": "minimax",
  "minimax_tts": {
    "api_key_env": "MINIMAX_API_KEY",
    "endpoint": "https://api.minimaxi.com/v1/t2a_v2",
    "model": "speech-2.8-hd",
    "voice_id": "Chinese (Mandarin)_Reliable_Executive",
    "voice_name": "可靠高管",
    "speed": 1.0,
    "context_adaptation": {
      "enabled": true,
      "default_context": "explanation",
      "profiles": {
        "explanation": {"speed_multiplier": 0.96, "volume_multiplier": 1.0, "pitch_offset": 0},
        "instruction": {"speed_multiplier": 0.93, "volume_multiplier": 1.02, "pitch_offset": 0},
        "warning": {"speed_multiplier": 0.9, "volume_multiplier": 1.08, "pitch_offset": -1},
        "call_to_action": {"speed_multiplier": 1.0, "volume_multiplier": 1.05, "pitch_offset": 1}
      }
    },
    "format": "mp3"
  },
  "kokoro_tts": {
    "api_url": "http://localhost:8880/v1/audio/speech",
    "voice": "zm_009",
    "speed": 1.0
  },
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

密钥不要写入配置文件。默认只读取本机环境变量：

```bash
export MINIMAX_API_KEY="你的本机 key"
```

## 依赖安装

```bash
# MiniMax 默认引擎不需要额外 Python 包，只需要环境变量
export MINIMAX_API_KEY="你的本机 key"

# 如需使用 Edge TTS
pip install edge-tts

# 如需使用 Kokoro TTS，启动本地 Docker 服务
cd /Users/m/document/QNSZ/project/kokoro-tts && ./start.sh

# 验证安装
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py --list-voices
```

## 输出文件

- 默认输出位置：与输入文件相同目录
- 默认文件名：`<原文件名>_tts.mp3`
- 如果启用后处理：`<原文件名>_tts_voice_changed.mp3`

## 性能参考

- MiniMax TTS: 取决于 API 响应速度和文本长度
- Kokoro TTS: 1000 字约 3-5 秒（本地 Docker CPU）
- Edge TTS: 1000 字约 10-20 秒（受网络影响）

## 注意事项

1. **密钥要求**：MiniMax 默认引擎需要 `MINIMAX_API_KEY` 环境变量
2. **文本长度**：建议单次转换不超过 10000 字
3. **脚本格式**：支持纯文本和带注释的播客脚本
4. **后处理**：需要先安装 voice-changer skill

## 故障排除

**问题: 网络连接失败**
- 检查网络连接
- MiniMax/Edge 可检查代理或 API 可用性
- Kokoro 连接 localhost 时必须绕过代理

**问题: MiniMax 报缺少 Key**
- 设置 `MINIMAX_API_KEY` 环境变量
- 不要把真实 Key 写入 `config/tts_config.json`

**问题: 声音不自然**
- 尝试调整语速和音调
- 更换不同的声音

**问题: 后处理失败**
- 确认 voice-changer skill 已安装
- 检查 voice-changer 配置

## 更新记录

### v3.3.1 (2026-07-18)
- 移除 MiniMax 逐 beat emotion 注入，避免连续句子语气不一致
- 保留 speed、volume、pitch 三项 MiniMax 专属语境调整
- 修复 payload 隔离测试并同步配置说明

### v3.3.0 (2026-07-18)
- MiniMax 默认音色改为 `Chinese (Mandarin)_Reliable_Executive`
- 增加 MiniMax 专属自动语境适配层和可选 `--context`
- 语境适配只修改 MiniMax 请求；Edge/Kokoro 保持原行为
- 增加自动识别、请求参数和跨引擎隔离测试

### v3.2.0 (2026-07-17)
- 新增 MiniMax TTS 引擎并设为默认
- 默认音色 `male-qn-jingying`（精英青年），语速 1.0
- API Key 只读取 `MINIMAX_API_KEY` 环境变量，防止密钥入库
- 保留 Kokoro/Edge，可通过 `tts_engine` 或 `--engine` 切换

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
