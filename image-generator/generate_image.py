#!/usr/bin/env python3
"""
通用图片生成 Skill
支持多种 AI 模型（ModelScope、Gemini 等）
可被其他 Skills 导入调用
"""

import requests
import time
import json
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageGenerator:
    """通用图片生成器"""

    def __init__(self, api_type: str = "modelscope", config_path: Optional[Path] = None):
        """
        初始化图片生成器

        Args:
            api_type: API 类型 ("modelscope" 或 "gemini")
            config_path: 配置文件路径
        """
        self.api_type = api_type
        self.config = self._load_config(config_path)
        self.api_config = self.config.get(api_type, {})

        if not self.api_config:
            raise ValueError(f"未找到 {api_type} 的配置")

    def _load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            config_path = Path.home() / ".claude/skills/image-generator/config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 返回默认配置
        return {
            "default_api": "modelscope",
            "modelscope": {
                "base_url": "https://api-inference.modelscope.cn/",
                "api_key": "",
                "model": "Tongyi-MAI/Z-Image-Turbo",
                "timeout": 300,
                "poll_interval": 5
            },
            "gemini": {
                "api_key": "",
                "model": "gemini-2.0-flash",
                "timeout": 60
            },
            "output_dir": str(Path.home() / "Downloads/shell/work/generated_images"),
            "image_format": "jpg",
            "quality": 95
        }

    def generate(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        test_mode: bool = False
    ) -> str:
        """
        生成图片

        Args:
            prompt: 图片描述
            output_path: 输出路径
            model: 指定模型
            size: 图片尺寸
            quality: 生成质量
            style: 风格
            timeout: 超时时间
            max_retries: 最大重试次数
            test_mode: 测试模式（生成示例图片）

        Returns:
            生成的图片路径
        """
        if test_mode:
            return self._generate_test_image(prompt, output_path, size)

        if self.api_type == "modelscope":
            return self._generate_modelscope(
                prompt, output_path, model, size, quality, style, timeout, max_retries
            )
        elif self.api_type == "gemini":
            return self._generate_gemini(
                prompt, output_path, model, size, quality, style, timeout, max_retries
            )
        else:
            raise ValueError(f"不支持的 API 类型: {self.api_type}")

    def _generate_test_image(self, prompt: str, output_path: Optional[str] = None, size: str = "1024x1024") -> str:
        """生成测试用的示例图片"""
        logger.info(f"📝 测试模式：生成示例图片")
        logger.info(f"   提示词: {prompt[:50]}...")

        # 解析尺寸
        width, height = map(int, size.split('x'))

        # 创建图片
        image = Image.new('RGB', (width, height), color=(73, 109, 137))
        draw = ImageDraw.Draw(image)

        # 添加文本
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            # 使用默认字体
            font = ImageFont.load_default()
            small_font = font

        # 绘制标题
        draw.text((50, 50), "Generated Image (Test Mode)", fill=(255, 255, 255), font=font)

        # 绘制提示词
        y_offset = 150
        for line in prompt.split('\n')[:5]:
            draw.text((50, y_offset), line[:80], fill=(200, 200, 200), font=small_font)
            y_offset += 40

        # 保存图片
        if output_path is None:
            output_dir = Path(self.config.get("output_dir", "~/Downloads/shell/work/generated_images")).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_format = self.config.get("image_format", "jpg")
            output_path = output_dir / f"test_image_{timestamp}.{image_format}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        quality = self.config.get("quality", 95)
        image.save(str(output_path), quality=quality)

        logger.info(f"💾 测试图片已保存: {output_path}")
        return str(output_path)

    def _generate_modelscope(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3
    ) -> str:
        """使用 ModelScope API 生成图片"""

        base_url = self.api_config.get("base_url")
        api_key = self.api_config.get("api_key")
        model = model or self.api_config.get("model")
        timeout = timeout or self.api_config.get("timeout", 300)
        poll_interval = self.api_config.get("poll_interval", 5)

        if not api_key:
            raise ValueError("ModelScope API Key 未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 构建请求体
        request_body = {
            "model": model,
            "prompt": prompt
        }

        logger.info(f"📝 开始生成图片: {prompt[:50]}...")
        logger.info(f"   模型: {model}")

        # 提交异步任务
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{base_url}v1/images/generations",
                    headers={**headers, "X-ModelScope-Async-Mode": "true"},
                    data=json.dumps(request_body, ensure_ascii=False).encode('utf-8'),
                    timeout=30
                )
                response.raise_for_status()
                task_id = response.json()["task_id"]
                logger.info(f"✅ 任务已提交: {task_id}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  提交失败，重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise

        # 轮询任务状态
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"生成超时 ({timeout}秒)")

            try:
                result = requests.get(
                    f"{base_url}v1/tasks/{task_id}",
                    headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
                    timeout=30
                )
                result.raise_for_status()
                data = result.json()

                if data["task_status"] == "SUCCEED":
                    logger.info("✅ 图片生成成功")
                    image_url = data["output_images"][0]
                    return self._save_image(image_url, output_path)

                elif data["task_status"] == "FAILED":
                    raise RuntimeError("图片生成失败")

                else:
                    logger.info(f"⏳ 生成中... ({elapsed:.0f}s)")
                    time.sleep(poll_interval)

            except Exception as e:
                logger.error(f"❌ 轮询失败: {e}")
                raise

    def _generate_gemini(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3
    ) -> str:
        """使用 Gemini API 生成图片"""

        api_key = self.api_config.get("api_key")
        model = model or self.api_config.get("model")
        timeout = timeout or self.api_config.get("timeout", 60)

        if not api_key:
            raise ValueError("Gemini API Key 未配置")

        import google.generativeai as genai

        genai.configure(api_key=api_key)

        logger.info(f"📝 开始生成图片: {prompt[:50]}...")
        logger.info(f"   模型: {model}")

        for attempt in range(max_retries):
            try:
                response = genai.ImageGenerationModel(model).generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    safety_filter_level="block_none",
                    aspect_ratio="1:1",
                    quality_tier="standard"
                )

                logger.info("✅ 图片生成成功")
                image = response.images[0]
                return self._save_image_from_pil(image, output_path)

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  生成失败，重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise

    def _save_image(self, image_url: str, output_path: Optional[str] = None) -> str:
        """保存图片"""

        # 下载图片
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))

        # 确定输出路径
        if output_path is None:
            output_dir = Path(self.config.get("output_dir", "~/Downloads/shell/work/generated_images")).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_format = self.config.get("image_format", "jpg")
            output_path = output_dir / f"image_{timestamp}.{image_format}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存图片
        quality = self.config.get("quality", 95)
        image.save(str(output_path), quality=quality)

        logger.info(f"💾 图片已保存: {output_path}")
        return str(output_path)

    def _save_image_from_pil(self, image: Image.Image, output_path: Optional[str] = None) -> str:
        """保存 PIL 图片对象"""

        # 确定输出路径
        if output_path is None:
            output_dir = Path(self.config.get("output_dir", "~/Downloads/shell/work/generated_images")).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_format = self.config.get("image_format", "jpg")
            output_path = output_dir / f"image_{timestamp}.{image_format}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存图片
        quality = self.config.get("quality", 95)
        image.save(str(output_path), quality=quality)

        logger.info(f"💾 图片已保存: {output_path}")
        return str(output_path)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="通用图片生成 Skill"
    )
    parser.add_argument("prompt", help="图片描述")
    parser.add_argument("--output", help="输出路径")
    parser.add_argument("--api-type", default="modelscope", help="API 类型 (modelscope/gemini)")
    parser.add_argument("--model", help="指定模型")
    parser.add_argument("--size", default="1024x1024", help="图片尺寸")
    parser.add_argument("--quality", default="standard", help="生成质量")
    parser.add_argument("--style", help="风格")
    parser.add_argument("--timeout", type=int, help="超时时间（秒）")
    parser.add_argument("--test", action="store_true", help="测试模式")

    args = parser.parse_args()

    try:
        generator = ImageGenerator(api_type=args.api_type)
        image_path = generator.generate(
            prompt=args.prompt,
            output_path=args.output,
            model=args.model,
            size=args.size,
            quality=args.quality,
            style=args.style,
            timeout=args.timeout,
            test_mode=args.test
        )
        print(f"✅ 图片生成完成: {image_path}")
    except Exception as e:
        logger.error(f"❌ 生成失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
