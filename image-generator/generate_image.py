#!/usr/bin/env python3
"""
通用图片生成 Skill
支持多种 AI 模型（ModelScope、Gemini、RunningHub 等）
可被其他 Skills 导入调用
"""

import requests
import time
import json
import sys
import argparse
import base64
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

    def __init__(self, api_type: Optional[str] = None, config_path: Optional[Path] = None):
        """
        初始化图片生成器

        Args:
            api_type: API 类型 ("modelscope"、"gemini" 或 "runninghub")。
                      为 None 时从 config.json 的 default_api 字段读取。
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        if api_type is None:
            default = self.config.get("default_api")
            if not default:
                raise ValueError(
                    "config.json 缺少 default_api 字段。请在配置文件中指定默认 API 类型，"
                    "例如: \"default_api\": \"runninghub\""
                )
            api_type = default
        self.api_type = api_type
        self.api_config = self.config.get(api_type, {})

        if not self.api_config:
            raise ValueError(f"未找到 {api_type} 的配置")

    def _load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            config_path = Path.home() / ".claude/skills/image-generator/config.json"

        if not config_path.exists():
            raise FileNotFoundError(
                f"image-generator 配置文件不存在: {config_path}\n"
                f"请创建配置文件，参考: {config_path}.example"
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

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
        elif self.api_type == "runninghub":
            return self._generate_runninghub(
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

    def _size_to_aspect_ratio(self, size: str) -> str:
        """Convert size string like '7680x4320' to aspect ratio like '16:9'."""
        try:
            w, h = map(int, size.lower().split("x"))
            from math import gcd
            g = gcd(w, h)
            return f"{w // g}:{h // g}"
        except Exception:
            return "1:1"

    def _gemini_image_size(self, size: str) -> str:
        """Map concrete dimensions to Gemini image_size presets."""
        try:
            w, h = map(int, size.lower().split("x"))
        except Exception:
            return "IMAGE_SIZE_1K"

        longest_edge = max(w, h)
        if longest_edge >= 4096:
            return "IMAGE_SIZE_4K"
        if longest_edge >= 2048:
            return "IMAGE_SIZE_2K"
        return "IMAGE_SIZE_1K"

    def _save_gemini_generated_image(self, generated_image: Any, output_path: Optional[str] = None) -> str:
        """Save a google.genai GeneratedImage object."""
        image_bytes = None
        image = getattr(generated_image, "image", None)
        if image is not None:
            raw_bytes = getattr(image, "image_bytes", None)
            if raw_bytes:
                image_bytes = raw_bytes
            else:
                data = getattr(image, "data", None)
                if data:
                    try:
                        image_bytes = base64.b64decode(data)
                    except Exception:
                        image_bytes = data if isinstance(data, (bytes, bytearray)) else None

        if not image_bytes:
            raise RuntimeError("Gemini 返回了结果，但未包含可保存的图片数据")

        pil_image = Image.open(BytesIO(image_bytes))
        return self._save_image_from_pil(pil_image, output_path)

    def _save_gemini_content_response_image(self, response: Any, output_path: Optional[str] = None) -> str:
        """Save image bytes from a Gemini generateContent response."""
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                data = getattr(inline_data, "data", None) if inline_data is not None else None
                if data:
                    pil_image = Image.open(BytesIO(data))
                    return self._save_image_from_pil(pil_image, output_path)
        raise RuntimeError("Gemini generateContent 未返回可保存的图片数据")

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

        if not model:
            raise ValueError("Gemini 模型未配置")

        normalized_model = model if str(model).startswith("models/") else f"models/{model}"
        use_generate_images = "imagen" in normalized_model.lower()
        use_generate_content_image = not use_generate_images

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        aspect_ratio = self._size_to_aspect_ratio(size)
        image_size = self._gemini_image_size(size)
        output_mime_type = "image/png" if str(output_path or "").lower().endswith(".png") else "image/jpeg"
        config = types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            output_mime_type=output_mime_type,
            safety_filter_level="BLOCK_ONLY_HIGH",
        )
        if use_generate_images:
            config.image_size = image_size

        logger.info(f"📝 开始生成图片: {prompt[:50]}...")
        logger.info(f"   模型: {normalized_model}, 画面比例: {aspect_ratio} ({size}), 输出尺寸档位: {image_size}")

        for attempt in range(max_retries):
            try:
                if use_generate_images:
                    response = client.models.generate_images(
                        model=normalized_model,
                        prompt=prompt,
                        config=config,
                    )
                    generated_images = getattr(response, "generated_images", None) or []
                    if not generated_images:
                        raise RuntimeError("Gemini/Imagen 未返回 generated_images")
                    logger.info("✅ 图片生成成功")
                    return self._save_gemini_generated_image(generated_images[0], output_path)

                if use_generate_content_image:
                    response = client.models.generate_content(
                        model=normalized_model,
                        contents=f"Create an image: {prompt}\n\nReturn the image directly. Do not return a text prompt, explanation, or markdown.",
                        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                    )
                    logger.info("✅ 图片生成成功")
                    return self._save_gemini_content_response_image(response, output_path)

                raise RuntimeError("不支持的 Gemini 图片生成模式")

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  生成失败，重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise


    def _generate_runninghub(
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
        """使用 RunningHub API 生成图片（文生图）"""

        base_url = self.api_config.get("base_url", "https://www.runninghub.cn/openapi/v2").rstrip("/")
        api_key = self.api_config.get("api_key")
        model = model or self.api_config.get("model")
        timeout = timeout or self.api_config.get("timeout", 300)
        poll_interval = self.api_config.get("poll_interval", 5)
        aspect_ratio = self._size_to_aspect_ratio(size)
        resolution = self.api_config.get("resolution", "2k")

        if not api_key:
            raise ValueError("RunningHub API Key 未配置")

        api_url = f"{base_url}/{model}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        request_body = {
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
        }

        logger.info(f"📝 开始生成图片: {prompt[:50]}...")
        logger.info(f"   模型: {model}, 画面比例: {aspect_ratio} ({size}), 清晰度: {resolution}")

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                task_id = data.get("taskId")
                status = (data.get("status") or "").upper()
                if not task_id:
                    raise RuntimeError(
                        f"RunningHub 未返回 taskId。响应: {json.dumps(data, ensure_ascii=False)[:500]}"
                    )

                logger.info(f"✅ 任务已提交: {task_id} ({status})")
                return self._poll_runninghub_task(
                    task_id=task_id,
                    headers=headers,
                    base_url=base_url,
                    timeout=timeout,
                    poll_interval=poll_interval,
                    output_path=output_path,
                )

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  生成失败，重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise

    def _poll_runninghub_task(
        self,
        task_id: str,
        headers: Dict[str, str],
        base_url: str,
        timeout: int,
        poll_interval: int,
        output_path: Optional[str] = None,
    ) -> str:
        """轮询 RunningHub 异步任务直到完成"""
        start_time = time.time()
        task_url = f"{base_url}/query"

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"RunningHub 生成超时 ({timeout}秒)")

            result = requests.post(
                task_url,
                headers=headers,
                data=json.dumps({"taskId": task_id}, ensure_ascii=False).encode("utf-8"),
                timeout=30,
            )
            result.raise_for_status()
            data = result.json()
            status = (data.get("status") or "").upper()

            if status == "SUCCESS":
                results = data.get("results")
                if results and isinstance(results, list) and len(results) > 0:
                    image_url = results[0].get("url")
                    if image_url:
                        logger.info("✅ 图片生成成功")
                        return self._save_image(image_url, output_path)
                raise RuntimeError(
                    f"RunningHub 任务成功但未返回图片: {json.dumps(data, ensure_ascii=False)[:500]}"
                )

            if status in {"FAILED", "FAIL", "ERROR", "CANCELLED", "CANCELED"}:
                raise RuntimeError(
                    f"RunningHub 任务失败: {json.dumps(data, ensure_ascii=False)[:500]}"
                )

            logger.info(f"⏳ RunningHub 生成中... ({elapsed:.0f}s, {status})")
            time.sleep(poll_interval)

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
        save_kwargs = {}
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        suffix = output_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            if image.mode == "RGBA":
                image = image.convert("RGB")
            save_kwargs["quality"] = quality
        image.save(str(output_path), **save_kwargs)

        logger.info(f"💾 图片已保存: {output_path}")
        return str(output_path)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="通用图片生成 Skill"
    )
    parser.add_argument("prompt", help="图片描述")
    parser.add_argument("--output", help="输出路径")
    parser.add_argument("--api-type", default=None, help="API 类型 (modelscope/gemini/runninghub)，未传时从 config.json 的 default_api 读取")
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
