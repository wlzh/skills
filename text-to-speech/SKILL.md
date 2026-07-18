---
name: text-to-speech
description: 文本转语音工具 - 默认 MiniMax TTS，支持切换 Edge TTS 和 Kokoro TTS (v1.1-zh)
version: 3.3.0
changelog:
  - 2026-07-18: v3.3.0 MiniMax 默认音色改为 Chinese (Mandarin)_Reliable_Executive；新增 MiniMax 专属语境适配层，按开场、总结、解释、步骤、提醒、资源、结论和关注引导自动微调表达；Edge/Kokoro 行为不变
  - 2026-07-17: v3.2.0 新增 MiniMax TTS 引擎并设为默认，默认音色 male-qn-jingying（精英青年）、语速 1.0；API Key 只读取 MINIMAX_API_KEY 环境变量；保留 Kokoro/Edge 可配置切换
  - 2026-05-17: v3.1.0 强化 localhost Kokoro 代理绕过规则——curl/requests 直连本地服务默认必须 NO_PROXY，不允许先走代理失败后重试

author: M.
---

# Text-to-Speech Skill

将文本转换为语音。默认使用 MiniMax TTS（在线高质量中文配音），并保留 Kokoro TTS v1.1-zh（本地 Docker，102 个中文音色）和 Edge TTS（在线）作为可配置后备。

## 引擎对比

| 特性 | MiniMax TTS | Kokoro TTS v1.1-zh | Edge TTS |
|------|-------------|-------------------|----------|
| 质量 | 默认推荐，中文短视频旁白更自然 | 本地可用、接近真人 | 标准 Neural 语音 |
| 网络 | 需要 MiniMax API | 不需要（本地 Docker） | 需要网络连接 |
| 默认音色 | `Chinese (Mandarin)_Reliable_Executive`（可靠高管） | `zm_009` | `zh-CN-YunyangNeural` |
| 语速调节 | speed 参数，默认 1.0 | speed 参数 | rate/pitch/volume |
| 前提 | `MINIMAX_API_KEY` 环境变量 | Docker 容器需运行 | 安装 `edge-tts` |
| 配置值 | `minimax` | `kokoro` | `edge` |

## 使用说明

```bash
# 默认使用 MiniMax TTS（当前配置）
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py <文本文件>

# 指定引擎
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --engine minimax
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --engine kokoro
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --engine edge

# 指定声音
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -v zf_094

# 指定输出文件
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -o output.mp3

# 调整语速（MiniMax/Kokoro）
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --speed 1.2

# 列出所有可用声音
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py --list-voices
```

## MiniMax TTS

默认配置：

- 引擎：`tts_engine = "minimax"`
- 模型：`speech-2.8-hd`
- 音色：`Chinese (Mandarin)_Reliable_Executive`（可靠高管）
- 语速：`1.0`
- 输出：MP3

### MiniMax 专属语境适配

`minimax_tts.context_adaptation` 只在 MiniMax 分支生效。Edge 和 Kokoro 不读取此配置，也不会改变原请求参数。

- 默认根据文本自动识别 `opening`、`summary`、`explanation`、`instruction`、`warning`、`resource`、`conclusion`、`call_to_action`、`neutral`
- 语境档只轻量调整 MiniMax 的语速、音量、音高和 emotion，不修改原文，不自动插入声音标签
- 未命中规则时使用 `explanation`
- 可用 `--context warning` 等参数显式覆盖自动识别；选择 Edge/Kokoro 时该参数被忽略
- 调用方无需理解语境规则。视频流水线只需继续提交文本并使用返回音频，音频时长仍由下游实测

```bash
# 自动识别语境
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt

# MiniMax 显式指定风险提醒语境
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt --context warning
```

密钥规则：

- API Key 只从环境变量读取，默认变量名 `MINIMAX_API_KEY`
- 不要把真实 Key 写进 `config/tts_config.json`、README、命令行参数或提交历史
- 如果要换变量名，只改 `config/tts_config.json` 中的 `minimax_tts.api_key_env`

```bash
export MINIMAX_API_KEY="你的本机 key"
python3 ~/.claude/skills/text-to-speech/scripts/text_to_speech.py script.txt -o output.mp3
```

## Kokoro TTS v1.1-zh 声音

使用 `--list-voices` 查看完整列表（102 个）。

### 推荐声音
- `zm_009` - 男声（默认）
- `zf_094` - 女声（自然温柔）
- `zf_001` - 女声
- `zm_050` - 男声

### 英文声音
- `af_maple` - 女声（Maple）
- `af_sol` - 女声（Sol）
- `bf_vale` - 男声（Vale）

### 声音命名规则
- `zf_XXX` - 中文女声（55 个）
- `zm_XXX` - 中文男声（44 个）
- `af_`/`bf_` - 英文声音（3 个）

## 启动 Kokoro 服务

Kokoro TTS 需要 Docker 容器运行：

```bash
# 启动
cd /Users/m/document/QNSZ/project/kokoro-tts && ./start.sh

# 停止
cd /Users/m/document/QNSZ/project/kokoro-tts && ./stop.sh

# Web UI 试听
# http://localhost:8880/web/
```

## 核心功能

### 1. 脚本解析
自动识别并移除播客脚本中的注释和标记：
- 时间戳：`(00:00)`
- BGM 注释：`[BGM渐入：...]`
- 舞台指示：`(主播声音：...)` `(停顿 1秒)`
- Markdown 标记：`**文本**`

### 2. 中英文混合朗读
v1.1-zh 模型支持中英文混合文本的自然朗读。

### 3. 后处理集成
可选集成 voice-changer skill 进行变声处理。

## 配置文件

配置文件位于：`~/.claude/skills/text-to-speech/config/tts_config.json`

关键配置项：
- `tts_engine`: `"minimax"`、`"kokoro"` 或 `"edge"`（默认引擎）
- `minimax_tts`: MiniMax 引擎配置（API URL、模型、默认音色、语速；Key 仅从环境变量读取）
- `minimax_tts.context_adaptation`: MiniMax 专属语境档和自动识别规则；不影响其他引擎
- `kokoro_tts`: Kokoro 引擎配置（API URL、默认声音、语速）
- `edge_tts`: Edge 引擎配置（声音、语速、音调、音量）
- `available_voices`: 按引擎分组的可用声音列表

## 工作流程

```
输入文本/文件
    ↓
脚本解析（移除注释和标记）
    ↓
MiniMax / Kokoro TTS / Edge TTS 语音合成
    ↓
后处理（voice-changer，可选）
    ↓
输出 MP3 文件
```

## 代理绕过（重要）

Kokoro TTS 运行在 `localhost:8880`。如果系统配置了 HTTP 代理（`http_proxy`/`https_proxy`），请求 localhost 会被代理拦截导致连接失败（curl 返回 HTTP 000）。

**规则**：
- Python 脚本已内置 `os.environ.setdefault("no_proxy", "localhost,127.0.0.1")`，通过脚本调用无需额外处理
- 如果 AI 需要直接用 `curl` 测试或调用 Kokoro API，**必须**加 `--noproxy localhost,127.0.0.1` 或设置 `no_proxy=localhost,127.0.0.1`
- 如果 AI 直接写 Python `requests.post("http://localhost:8880/...")`，必须设置 `proxies={"http": None, "https": None}`，或使用 `requests.Session(); session.trust_env = False`，并设置 `NO_PROXY/no_proxy=localhost,127.0.0.1,::1`
- 禁止不加代理绕过直接 curl/requests localhost；不要先走代理失败再重试，localhost Kokoro 请求默认就必须绕过代理

```bash
# 正确：绕过代理
curl --noproxy localhost,127.0.0.1 -X POST http://localhost:8880/v1/audio/speech ...

# 错误：走了代理，返回 HTTP 000
curl -X POST http://localhost:8880/v1/audio/speech ...
```

## 依赖

- MiniMax TTS: `MINIMAX_API_KEY` 环境变量
- Kokoro TTS: Docker（容器运行在 localhost:8880）
- Edge TTS: `pip install edge-tts`

## 性能参考

- Kokoro TTS: 1000字约 3-5 秒（本地 Docker CPU）
- Edge TTS: 1000字约 10-20 秒（受网络影响）
