# Image Generator Skill

通用图片生成 Skill，支持多种 AI 模型，可被其他 Skills 直接调用。

## 快速开始

### 1. 命令行使用

```bash
# 基本用法
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat"

# 自定义输出路径
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --output ~/my_image.jpg

# 指定 API 类型
python3 ~/.claude/skills/image-generator/generate_image.py "A golden cat" --api-type modelscope
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

编辑 `~/.claude/skills/image-generator/config.json`：

```json
{
  "default_api": "modelscope",
  "modelscope": {
    "base_url": "https://api-inference.modelscope.cn/",
    "api_key": "your-token-here",
    "model": "Tongyi-MAI/Z-Image-Turbo",
    "timeout": 300,
    "poll_interval": 5
  },
  "output_dir": "~/Downloads/shell/work/generated_images",
  "image_format": "jpg",
  "quality": 95
}
```

## 支持的 API

### ModelScope
- 高速图片生成
- 支持异步任务
- 需要 API Token

### Gemini
- Google Gemini 2.0 Flash
- 需要 API Key

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
        prompt: str,                    # 图片描述
        output_path: Optional[str] = None,  # 输出路径
        model: Optional[str] = None,    # 指定模型
        size: str = "1024x1024",        # 图片尺寸
        quality: str = "standard",      # 生成质量
        style: Optional[str] = None,    # 风格
        timeout: Optional[int] = None,  # 超时时间
        max_retries: int = 3            # 最大重试次数
    ) -> str:                           # 返回图片路径
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
