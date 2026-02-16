# RVC 模型下载与使用指南

## 概述

RVC (Retrieval-based Voice Conversion) 需要以下组件才能正常工作：

1. **RVC 模型文件** (.pth) - 主要的语音转换模型
2. **HuBERT 模型** (hubert_base.pt) - 用于提取音频特征 (~600MB)
3. **可选: Index 文件** (.index) - 提高转换质量

## 模型下载方式

### 方式 0: 260款RVC变声器模型（推荐）

**260款RVC变声器模型** - 包含多种声音类型：
- 链接: https://pan.quark.cn/s/1cf1c5d6d4a6
- 优点: 模型丰富，一次下载多个选择

### 方式 1: Hugging Face（推荐）

1. 访问 [Hugging Face Models](https://huggingface.co/models)
2. 搜索 "RVC" 或 "voice conversion"
3. 选择一个模型，下载 `.pth` 文件

**推荐模型源**:
- [RVC-Project Models](https://huggingface.co/Rvcmodel)
- [Community RVC Models](https://huggingface.co/models?search=RVC)

### 方式 2: ModelScope（国内镜像）

1. 访问 [ModelScope](https://modelscope.cn/models)
2. 搜索 "RVC"
3. 下载模型文件

### 方式 3: 直接下载 HubERT 模型

```bash
# HubERT 基础模型（必需）
cd ~/.claude/skills/voice-changer/models/rvc_models
wget https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/assets/hubert/hubert_base.pt
```

## 安装步骤

### 1. 确保已克隆 RVC 代码

```bash
cd ~/.claude/skills/voice-changer/models
git clone --depth 1 https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
```

### 2. 创建模型目录

```bash
mkdir -p ~/.claude/skills/voice-changer/models/rvc_models/my_model
```

### 3. 下载模型文件

将下载的 `.pth` 文件放到 `rvc_models/my_model/` 目录下

### 4. 配置模型路径

编辑 `~/.claude/skills/voice-changer/config/voice_config.json`:

```json
{
  "voices": {
    "rvc_my_model": {
      "name": "我的 RVC 模型",
      "description": "使用 RVC 进行变声",
      "method": "rvc",
      "model_path": "/Users/你的用户名/.claude/skills/voice-changer/models/rvc_models/my_model/model.pth",
      "index_path": "/Users/你的用户名/.claude/skills/voice-changer/models/rvc_models/my_model/model.index",
      "f0up_key": 0
    }
  }
}
```

### 5. 使用 RVC 变声

```bash
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py \
  input.mp3 \
  -v rvc_my_model \
  -m rvc
```

## 当前状态

✅ **已完成**:
- RVC 代码已克隆到本地
- 核心依赖已安装（PyTorch, librosa, pyworld 等）
- RVC 接口已集成到 voice-changer skill

⚠️ **需要用户完成**:
- 下载 RVC 模型文件 (.pth)
- 下载 HuBERT 模型 (hubert_base.pt, ~600MB)
- 配置模型路径

## 临时替代方案

在模型下载完成之前，可以使用 **增强版 Pedalboard** 方法：

```bash
# 默认使用增强版 Pedalboard（推荐）
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3

# 或显式指定
python3 ~/.claude/skills/voice-changer/scripts/voice_change.py input.mp3 -m pedalboard
```

增强版 Pedalboard 特点：
- ✅ 高质量音高变换
- ✅ 音色调整（滤波器、压缩器）
- ✅ 依赖简单
- ✅ 速度快

## 常见问题

### Q: 为什么不自动下载模型？

A: RVC 模型文件较大（50-600MB），且需要用户选择合适的声音模型。手动下载可以让用户：
1. 选择喜欢的声音
2. 了解模型的使用许可
3. 控制下载位置

### Q: RVC 和 Pedalboard 的区别？

A:
- **Pedalboard**: 音高 + 音色调整，快速，依赖简单
- **RVC**: AI 深度学习模型，真正的声音转换，效果更好但需要额外下载

### Q: 如何获得更好的效果？

A:
1. 使用高质量的输入音频
2. 选择与输入声音性别相近的模型
3. 调整 f0up_key 参数（音高偏移）
4. 使用 GPU 加速（如果可用）
