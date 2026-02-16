# Image Generator Skill

> **版本**: v1.1.0

通用图片生成 Skill，支持多种 AI 模型，可被其他 Skills 直接调用。

## 功能特性

- 🎨 支持多种 AI 模型（ModelScope、Gemini 等）
- 📦 可作为库被其他 Skills 导入调用
- ⚙️ 灵活的配置系统
- 🔄 异步任务支持（ModelScope）
- 💾 自动保存生成的图片
- 🛡️ 错误处理和重试机制
- 🧪 测试模式支持（无需 API Key）

## 快速开始

### 1. 命令行使用

```bash
# 基本用法（默认使用 gemini）
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat"

# 指定 API 类型
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --api-type modelscope

# 自定义输出路径
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --output ~/my_image.jpg

# 测试模式（无需 API Key）
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --test
```

### 2. 在其他 Skills 中导入使用

```python
import sys
from pathlib import Path

# 添加 image-generator 到路径
sys.path.insert(0, str(Path.home() / ".claude/skills/image-generator"))

from generate_image import ImageGenerator

# 创建生成器
generator = ImageGenerator(api_type="modelscope")

# 生成图片
image_path = generator.generate(
    prompt="A beautiful landscape",
    output_path="/path/to/output.jpg"
)

print(f"图片已生成: {image_path}")
```

## 配置

### 首次使用配置

1. 复制配置模板文件：
```bash
cp ~/.claude/skills/image-generator/config.json.example ~/.claude/skills/image-generator/config.json
```

2. 编辑 `~/.claude/skills/image-generator/config.json` 填入你的 API Key：

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
  "output_dir": "~/Downloads/shell/work/generated_images",
  "image_format": "jpg",
  "quality": 95
}
```

### 配置说明

- `default_api`: 默认使用的 API（`modelscope` 或 `gemini`）
- `modelscope.api_key`: ModelScope API Token（从 https://modelscope.cn 获取）
- `gemini.api_key`: Google Gemini API Key（从 https://ai.google.dev 获取）
- `gemini.model`: Gemini 模型名称（如 `gemini-3-pro-image-preview`）
- `output_dir`: 图片输出目录
- `image_format`: 图片格式（`jpg`、`png`、`webp`）
- `quality`: 图片质量（1-100）

**注意**：`config.json` 包含敏感信息，已被 `.gitignore` 忽略，不会提交到版本库

## 支持的 API

### ModelScope
- 高速图片生成
- 支持异步任务
- 需要 API Token

### Gemini
- Google Gemini 3 Pro 图片生成
- 需要 API Key

## 测试模式

无需配置 API Key 即可快速测试：

```bash
python3 ~/.claude/skills/image-generator/generate_image.py "A test image" --test
```

```python
# Python 中使用
generator = ImageGenerator()
image = generator.generate("A test image", test_mode=True)
```

## 在其他 Skills 中集成

### 示例：写文章 Skill 中生成封面

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / ".claude/skills/image-generator"))
from generate_image import ImageGenerator

def write_article_with_cover(title, content):
    # 生成文章
    article = f"# {title}\n\n{content}"

    # 生成封面图片
    generator = ImageGenerator()
    cover_image = generator.generate(
        prompt=f"Professional article cover for: {title}",
        output_path=f"./covers/{title}.jpg"
    )

    return {
        "article": article,
        "cover": cover_image
    }
```

## 运行示例

```bash
# 示例 1：基本使用
python3 ~/.claude/skills/image-generator/examples.py --example 1

# 示例 2：自定义输出
python3 ~/.claude/skills/image-generator/examples.py --example 2

# 示例 3：生成文章封面
python3 ~/.claude/skills/image-generator/examples.py --example 3

# 示例 4：批量生成
python3 ~/.claude/skills/image-generator/examples.py --example 4

# 示例 5：与其他 Skill 集成
python3 ~/.claude/skills/image-generator/examples.py --example 5
```

## API 参考

### ImageGenerator 类

```python
class ImageGenerator:
    def __init__(self, api_type: str = "modelscope", config_path: Optional[Path] = None)

    def generate(
        self,
        prompt: str,                         # 图片描述
        output_path: Optional[str] = None,   # 输出路径
        model: Optional[str] = None,         # 指定模型
        size: str = "1024x1024",             # 图片尺寸
        quality: str = "standard",           # 生成质量
        style: Optional[str] = None,         # 风格
        timeout: Optional[int] = None,        # 超时时间
        max_retries: int = 3,                # 最大重试次数
        test_mode: bool = False               # 测试模式
    ) -> str:                                # 返回图片路径
```

## 文件结构

```
image-generator/
├── SKILL.md                 # Skill 文档
├── README.md               # 本文件
├── config.json             # 配置文件
├── generate_image.py       # 主模块
├── examples.py             # 使用示例
└── scripts/                # 脚本目录
```

## 常见问题

### Q: 如何在 Skill 中导入？
A: 使用以下代码：
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/image-generator"))
from generate_image import ImageGenerator
```

### Q: 生成超时怎么办？
A: 增加 config.json 中的 timeout 值，或在 generate() 中传递 timeout 参数。

### Q: 支持哪些图片格式？
A: 支持 JPG、PNG、WebP 等，在 config.json 中配置 image_format。

### Q: 如何处理生成失败？
A: 使用 try-except 捕获异常，自动重试机制会尝试 3 次。

## 许可证

MIT
