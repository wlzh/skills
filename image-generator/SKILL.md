---
name: image-generator
description: 通用图片生成 Skill，支持多种 AI 模型（ModelScope、Gemini、RunningHub 等），可被其他 Skills 调用
version: 1.1.0
author: M.
---

# 图片生成 Skill

通用的图片生成服务，支持多种 AI 模型，可被其他 Skills 直接调用。

## 功能特性

- 🎨 支持多种 AI 模型（ModelScope、Gemini、RunningHub 等）
- 📦 可作为库被其他 Skills 导入调用
- ⚙️ 灵活的配置系统
- 🔄 异步任务支持（ModelScope、RunningHub）
- 💾 自动保存生成的图片
- 🛡️ 错误处理和重试机制
- 🧪 测试模式支持（无需 API Key）

## 使用方式

### 方式 1：直接命令行调用

```bash
# 基本用法（默认使用 gemini）
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat"

# 指定 API 类型
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --api-type modelscope

# RunningHub 文生图
python3 ~/.claude/skills/image-generator/generate_image.py \
  "一只金色的猫在阳光下打盹" \
  --api-type runninghub

# 指定输出路径
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --output /path/to/image.jpg

# 指定模型
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --model "Tongyi-MAI/Z-Image-Turbo"

# 测试模式（无需 API Key）
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --test
```

### 方式 2：在其他 Skills 中导入调用

```python
import sys
from pathlib import Path

# 添加 image-generator skill 到路径
image_gen_path = Path.home() / ".claude/skills/image-generator"
sys.path.insert(0, str(image_gen_path))

from generate_image import ImageGenerator

# 创建生成器实例
generator = ImageGenerator(api_type="modelscope")

# 生成图片
image_path = generator.generate(
    prompt="A beautiful landscape",
    output_path="/path/to/output.jpg"
)

print(f"图片已生成: {image_path}")
```

```python
# RunningHub 文生图示例
from generate_image import ImageGenerator

generator = ImageGenerator(api_type="runninghub")
image_path = generator.generate(
    prompt="一只金色的猫在阳光下打盹",
    output_path="/path/to/output.jpg"
)
```

## 配置

### 首次使用配置

1. 复制配置模板文件：
```bash
cp ~/.claude/skills/image-generator/config.json.example ~/.claude/skills/image-generator/config.json
```

2. 编辑配置文件填入你的 API Key：

配置文件位于：`~/.claude/skills/image-generator/config.json`

```json
{
  "default_api": "gemini",
  "modelscope": {
    "base_url": "https://api-inference.modelscope.cn/",
    "api_key": "your-modelscope-token-here",
    "model": "Tongyi-MAI/Z-Image-Turbo",
    "timeout": 300,
    "poll_interval": 5
  },
  "gemini": {
    "api_key": "your-gemini-api-key-here",
    "model": "gemini-3-pro-image-preview",
    "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent",
    "timeout": 120,
    "size": "1024x1024",
    "quality": "standard"
  },
  "runninghub": {
    "base_url": "https://www.runninghub.cn/openapi/v2",
    "api_key": "your-runninghub-api-key-here",
    "model": "rhart-image-n-g31-flash/text-to-image",
    "timeout": 300,
    "poll_interval": 5,
    "resolution": "2k"
  },
  "output_dir": "~/Downloads/shell/work/generated_images",
  "image_format": "jpg",
  "quality": 95
}
```

### 配置参数说明

**通用配置**：
- `default_api`: 默认使用的 API（`modelscope`、`gemini` 或 `runninghub`）
- `output_dir`: 图片输出目录
- `image_format`: 图片格式（`jpg`、`png`、`webp`）
- `quality`: 图片质量（1-100）

**ModelScope 配置**：
- `base_url`: ModelScope API 地址
- `api_key`: ModelScope API Token（从 https://modelscope.cn 获取）
- `model`: 使用的模型名称
- `timeout`: 请求超时时间（秒）
- `poll_interval`: 轮询间隔（秒）

**Gemini 配置**：
- `api_key`: Google Gemini API Key（从 https://ai.google.dev 获取）
- `model`: 使用的模型名称（如 `gemini-3-pro-image-preview`）
- `api_url`: API 端点地址
- `timeout`: 请求超时时间（秒）
- `size`: 图片尺寸（如 `1024x1024`）
- `quality`: 生成质量（`standard` 或 `high`）

**RunningHub 配置**：
- `base_url`: RunningHub OpenAPI 地址
- `api_key`: RunningHub API Key
- `model`: 使用的模型路径（如 `rhart-image-n-g31-flash/text-to-image`）
- `timeout`: 请求超时时间（秒）
- `poll_interval`: 轮询间隔（秒）
- `resolution`: 默认分辨率（如 `2k`）

**注意**：
- `config.json` 包含敏感的 API Key，已被 `.gitignore` 忽略
- 不要将包含真实 API Key 的配置文件提交到版本库
- 使用 `config.json.example` 作为模板参考

## 支持的模型

### ModelScope
- `Tongyi-MAI/Z-Image-Turbo` - 高速图片生成
- `damo/text-to-image-synthesis` - 文本到图片
- 其他 ModelScope 支持的模型

### Gemini
- `gemini-3-pro-image-preview` - Gemini 3 Pro 图片生成
- 其他 Gemini 支持的模型

### RunningHub
- `rhart-image-n-g31-flash/text-to-image` - 文生图（2K 分辨率）
- 其他 RunningHub OpenAPI 兼容模型

## API 参数

### generate() 方法

```python
generator.generate(
    prompt: str,                    # 图片描述（必需）
    output_path: str = None,         # 输出路径（可选）
    model: str = None,               # 指定模型（可选）
    size: str = "1024x1024",         # 图片尺寸
    quality: str = "standard",       # 生成质量
    style: str = None,               # 风格（可选）
    timeout: int = 300,              # 超时时间（秒）
    max_retries: int = 3,            # 最大重试次数
    test_mode: bool = False          # 测试模式
) -> str                             # 返回图片路径
```

## 错误处理

- 自动重试失败的请求（最多 3 次）
- 详细的错误日志
- 优雅的降级处理

## 测试模式

支持测试模式，无需配置 API Key 即可快速测试图片生成流程：

```bash
# 命令行使用测试模式
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --test
```

```python
# Python 代码中使用测试模式
generator = ImageGenerator(api_type="gemini")
image_path = generator.generate(
    prompt="A beautiful landscape",
    test_mode=True  # 启用测试模式
)
```

测试模式会生成一张包含提示词内容的示例图片，适合在开发调试或无网络环境时使用。

## 示例

### 示例 1：基本使用

```bash
python3 ~/.claude/skills/image-generator/generate_image.py "A futuristic city"
```

### 示例 2：测试模式（无需 API Key）

```bash
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --test
```

### 示例 3：在 Python 中使用

```python
from generate_image import ImageGenerator

gen = ImageGenerator()
image = gen.generate("A beautiful sunset over the ocean")
print(f"Generated: {image}")
```

### 示例 4：在其他 Skill 中集成

```python
# 在 write-article skill 中
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / ".claude/skills/image-generator"))
from generate_image import ImageGenerator

def generate_article_cover(title):
    gen = ImageGenerator()
    cover_image = gen.generate(
        prompt=f"Professional article cover for: {title}",
        output_path=f"./covers/{title}.jpg"
    )
    return cover_image
```

## 注意事项

1. **API Key 配置**：
   - 需要在 config.json 中配置相应的 API Key
   - 不要将 API Key 提交到版本控制

2. **网络要求**：
   - 需要稳定的网络连接
   - 某些 API 可能需要科学上网

3. **生成时间**：
   - ModelScope 通常需要 10-30 秒
   - Gemini 通常需要 5-15 秒
   - RunningHub 通常需要 15-30 秒

4. **成本考虑**：
   - 某些 API 可能产生费用
   - 建议监控 API 使用情况

5. **输出格式**：
   - 支持 JPG、PNG、WebP 等格式
   - 默认输出为 JPG 格式

## 故障排除

### 问题 1：API Key 无效
```
错误: Unauthorized
解决: 检查 config.json 中的 API Key 是否正确
```

### 问题 2：生成超时
```
错误: Timeout
解决: 增加 config.json 中的 timeout 值
```

### 问题 3：网络连接失败
```
错误: Connection Error
解决: 检查网络连接，某些 API 可能需要科学上网
```

## 依赖

- requests
- Pillow (PIL)
- 其他 Skills 可选依赖

## 许可证

MIT
