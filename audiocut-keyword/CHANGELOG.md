# Changelog

## v1.1.0 - 2026-01-22

### 🐛 重要修复

- ✅ **Python 3.10 FunASR 环境支持** - 解决 Python 3.11 兼容性问题
  - 新增 `funasr_env_310/` Python 3.10 隔离环境
  - 安装 torch 2.10.0 和 funasr 1.3.0
  - 使用清华镜像源加速安装

### 🔧 技术细节

**FunASR 兼容性问题**：
```
错误: ValueError: mutable default for field override_dirname
原因: FunASR 的 hydra 依赖与 Python 3.11 dataclass 不兼容
解决: 创建 Python 3.10 隔离环境
```

**环境路径**：
- FunASR 环境：`~/.claude/skills/audiocut-keyword/funasr_env_310/`
- Python 解释器：`funasr_env_310/bin/python3`

### 📝 集成更新

**youtube-to-xiaoyuzhou 集成**：
- 自动检测 FunASR Python 3.10 环境
- 优先使用隔离环境运行关键字过滤
- 向下兼容：环境不存在时使用系统 Python

### ✨ 使用方式

**直接使用（推荐）**：
```bash
# 使用 FunASR Python 3.10 环境
~/.claude/skills/audiocut-keyword/funasr_env_310/bin/python3 \
  ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py input.mp3
```

**youtube-to-xiaoyuzhou 集成**：
```bash
# 自动使用 FunASR 环境
/youtube-to-xiaoyuzhou https://youtu.be/xxxxx --filter-keywords
```

## v1.0.0 - 2026-01-19

### 🎉 首次发布

**音频关键字过滤工具** - 基于 FunASR 语音识别和 FFmpeg 剪辑的音频关键字过滤 Skill

### ✨ 核心功能

- ✅ **精确转录** - 使用 FunASR Paraformer 进行 30s 分段转录
- ✅ **字符级时间戳** - 获取毫秒级精确时间戳
- ✅ **关键字识别** - 根据配置文件自动识别音频中的关键字
- ✅ **智能剪辑** - 使用 FFmpeg 精确删除关键字片段并合成最终音频
- ✅ **可配置** - 支持自定义关键字列表和缓冲时间

### 🔧 技术实现

**转录引擎**:
- FunASR Paraformer 模型（中文语音识别）
- 30s 分段策略，避免长音频时间戳漂移
- 字符级时间戳精度（毫秒级）
- JSON 格式输出

**关键字识别**:
- 正则表达式匹配
- 字符位置到时间戳映射
- 上下文信息记录

**音频剪辑**:
- FFmpeg filter_complex 无损剪辑
- 自动合并重叠片段
- 保留原始音频质量

### 📊 性能指标

- 转录速度: ~0.16x 实时（1分钟音频约10秒处理）
- 剪辑速度: 几乎瞬时完成
- 15分钟音频: 总处理时间约 2-3 分钟

*测试环境: M1 Mac，CPU 推理*

### 📦 输出文件

- `<原文件名>_filtered.mp3` - 处理后的音频
- `<原文件名>_delete_plan.json` - 删除计划（包含匹配信息）
- `<原文件名>_transcript.json` - 转录文件（可选保留）

### 🎯 使用场景

1. **YouTube 转播客** - 删除视频中的"关注"、"订阅"、"点赞"等引导语
2. **广告过滤** - 自动删除音频中的广告和推广内容
3. **内容清理** - 批量处理音频，删除不需要的关键字片段

### 📝 配置文件

默认配置文件: `config/keywords.json`

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

### 📚 依赖要求

**Python 依赖**:
- funasr
- modelscope

**系统依赖**:
- FFmpeg (音频处理)
- ffprobe (音频信息获取)

### 🔮 未来计划

- [ ] 支持模糊匹配和正则表达式
- [ ] 支持多语言（英文、日文等）
- [ ] 添加 GUI 界面
- [ ] 支持实时预览删除效果
- [ ] 集成到更多播客工作流

### 📄 许可

MIT
