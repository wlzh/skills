#!/usr/bin/env python3
"""
示例：在其他 Skills 中调用 image-generator
"""

import sys
from pathlib import Path

# 添加 image-generator skill 到路径
image_gen_path = Path.home() / ".claude/skills/image-generator"
sys.path.insert(0, str(image_gen_path))

from generate_image import ImageGenerator


def example_1_basic_usage():
    """示例 1：基本使用"""
    print("\n" + "="*60)
    print("示例 1：基本使用")
    print("="*60)

    generator = ImageGenerator(api_type="modelscope")
    image_path = generator.generate(
        prompt="A beautiful golden cat sitting on a sunny windowsill"
    )
    print(f"✅ 生成完成: {image_path}")


def example_2_custom_output():
    """示例 2：自定义输出路径"""
    print("\n" + "="*60)
    print("示例 2：自定义输出路径")
    print("="*60)

    generator = ImageGenerator(api_type="modelscope")
    output_path = Path.home() / "Downloads/my_generated_image.jpg"

    image_path = generator.generate(
        prompt="A futuristic city with flying cars",
        output_path=str(output_path)
    )
    print(f"✅ 生成完成: {image_path}")


def example_3_article_cover():
    """示例 3：为文章生成封面"""
    print("\n" + "="*60)
    print("示例 3：为文章生成封面")
    print("="*60)

    article_title = "The Future of Artificial Intelligence"
    article_summary = "Exploring how AI will transform industries and society"

    generator = ImageGenerator(api_type="modelscope")

    # 根据文章内容生成提示词
    prompt = f"Professional article cover image for '{article_title}': {article_summary}. Modern, clean design, high quality."

    output_dir = Path.home() / "Downloads/article_covers"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_path = generator.generate(
        prompt=prompt,
        output_path=str(output_dir / f"{article_title.replace(' ', '_')}_cover.jpg")
    )
    print(f"✅ 文章封面已生成: {image_path}")


def example_4_batch_generation():
    """示例 4：批量生成图片"""
    print("\n" + "="*60)
    print("示例 4：批量生成图片")
    print("="*60)

    prompts = [
        "A serene mountain landscape at sunset",
        "A modern office workspace with natural light",
        "A cozy coffee shop interior"
    ]

    generator = ImageGenerator(api_type="modelscope")
    output_dir = Path.home() / "Downloads/batch_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, prompt in enumerate(prompts, 1):
        print(f"\n生成第 {i}/{len(prompts)} 张图片...")
        try:
            image_path = generator.generate(
                prompt=prompt,
                output_path=str(output_dir / f"image_{i:02d}.jpg")
            )
            print(f"✅ 完成: {image_path}")
        except Exception as e:
            print(f"❌ 失败: {e}")


def example_5_integration_with_other_skill():
    """示例 5：与其他 Skill 集成"""
    print("\n" + "="*60)
    print("示例 5：与其他 Skill 集成")
    print("="*60)

    # 模拟从其他 Skill 接收的数据
    article_data = {
        "title": "Machine Learning Basics",
        "content": "An introduction to machine learning concepts and applications",
        "category": "Technology"
    }

    generator = ImageGenerator(api_type="modelscope")

    # 根据文章数据生成图片
    prompt = f"Professional {article_data['category']} article cover for '{article_data['title']}'. {article_data['content']}. High quality, modern design."

    try:
        image_path = generator.generate(
            prompt=prompt,
            output_path=str(Path.home() / f"Downloads/{article_data['title'].replace(' ', '_')}_cover.jpg")
        )
        print(f"✅ 图片已生成: {image_path}")

        # 返回图片路径供其他 Skill 使用
        return image_path
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="image-generator 使用示例")
    parser.add_argument(
        "--example",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="运行的示例编号"
    )

    args = parser.parse_args()

    try:
        if args.example == 1:
            example_1_basic_usage()
        elif args.example == 2:
            example_2_custom_output()
        elif args.example == 3:
            example_3_article_cover()
        elif args.example == 4:
            example_4_batch_generation()
        elif args.example == 5:
            example_5_integration_with_other_skill()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
