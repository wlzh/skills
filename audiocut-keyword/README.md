# 音频关键字过滤工具 (audiocut-keyword)

> 仓库地址: https://github.com/wlzh/skills
> 版本: v1.1.0

根据关键字配置自动识别并删除音频中的指定内容

## 快速使用

```bash
# 基本用法
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py <音频文件>

# 指定输出文件
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py input.mp3 -o output.mp3

# 使用自定义关键字配置
python3 ~/.claude/skills/audiocut-keyword/scripts/audiocut_keyword.py input.mp3 -k my_keywords.json
```

## 功能特性

- ✅ 使用 FunASR 进行精确转录（字符级时间戳）
- ✅ 根据配置文件自动识别关键字
- ✅ 使用 FFmpeg 精确剪辑并合成音频
- ✅ 支持自定义关键字和缓冲时间

## 工作流程

1. **转录音频** - FunASR 30s 分段转录
2. **识别关键字** - 在转录文本中查找关键字
3. **生成删除计划** - 合并重叠片段
4. **剪辑音频** - FFmpeg 执行删除并合成

## 配置文件

编辑 `config/keywords.json` 添加需要删除的关键字：

```json
{
  "keywords": [
    "广告",
    "赞助",
    "关注",
    "订阅",
    "点赞"
  ],
  "buffer_before": 0.5,
  "buffer_after": 0.5
}
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

### 手动安装

如需手动安装 FunASR：

```bash
# 创建 Python 3.10 虚拟环境
python3.10 -m venv ~/.claude/skills/audiocut-keyword/funasr_env_310

# 激活环境
source ~/.claude/skills/audiocut-keyword/funasr_env_310/bin/activate

# 使用清华镜像安装
pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install funasr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 系统依赖

```bash
# FFmpeg
brew install ffmpeg  # macOS
```

## 输出文件

处理完成后会生成以下文件:

- `<原文件名>_filtered.mp3` - 处理后的音频
- `<原文件名>_delete_plan.json` - 删除计划（包含匹配信息）
- `<原文件名>_transcript.json` - 转录文件

## 性能参考

- 转录速度: ~0.16x 实时（1分钟音频约10秒处理）
- 剪辑速度: 几乎瞬时完成
- 15分钟音频: 总处理时间约 2-3 分钟

*测试环境: M1 Mac，CPU 推理*

## 更新记录

### v1.1.0 (2026-01-22)
- ✅ **Python 3.10 FunASR 环境支持** - 解决 Python 3.11 兼容性问题
- ✅ **新增预配置环境** - `funasr_env_310/` 包含 torch 和 funasr
- ✅ **youtube-to-xiaoyuzhou 集成** - 自动检测并使用 FunASR 环境

### v1.0.0 (2026-01-19)
- 首次发布
- 使用 FunASR Paraformer 进行 30s 分段转录
- 支持字符级时间戳精确定位
- 使用 FFmpeg 进行无损音频剪辑
- 支持自定义关键字配置
- 支持可调节的缓冲时间

## 详细文档

查看 [SKILL.md](SKILL.md) 获取完整文档。

## License

MIT
