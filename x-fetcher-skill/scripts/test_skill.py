#!/usr/bin/env python3
"""
X Fetcher Skill 测试脚本
用于验证 Skill 的基本功能
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """测试导入依赖"""
    print("测试 1: 导入依赖...")
    try:
        import requests
        import yaml
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n测试 2: 配置文件...")
    try:
        from scripts.main import load_config
        config = load_config()

        if config:
            print(f"✅ 配置已加载")
            print(f"   - 默认输出目录: {config.get('default_output_dir', '未设置')}")
            print(f"   - 自动保存: {config.get('auto_save', '未设置')}")
            return True
        else:
            print("⚠️  未找到配置文件")
            print("   请运行: bash scripts/quick-start.sh")
            return False
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_fetch_x():
    """测试原始脚本"""
    print("\n测试 3: 原始脚本...")
    try:
        import fetch_x
        print("✅ 原始脚本导入成功")

        # 测试 URL 解析
        test_url = "https://x.com/elonmusk/status/123456789"
        tweet_id = fetch_x.extract_tweet_id(test_url)
        username = fetch_x.extract_username(test_url)

        if tweet_id == "123456789" and username == "elonmusk":
            print("✅ URL 解析正常")
            return True
        else:
            print(f"❌ URL 解析失败: tweet_id={tweet_id}, username={username}")
            return False
    except Exception as e:
        print(f"❌ 原始脚本测试失败: {e}")
        return False

def test_directory_creation():
    """测试目录创建"""
    print("\n测试 4: 目录创建...")
    try:
        from scripts.main import ensure_output_dir
        import tempfile
        import shutil

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            result_dir = ensure_output_dir(temp_dir, "test_user")
            expected_path = Path(temp_dir) / "test_user"

            if result_dir == expected_path and result_dir.exists():
                print("✅ 目录创建正常")
                return True
            else:
                print(f"❌ 目录创建失败: {result_dir}")
                return False
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"❌ 目录创建测试失败: {e}")
        return False

def test_markdown_generation():
    """测试 Markdown 生成"""
    print("\n测试 5: Markdown 生成...")
    try:
        import fetch_x

        # 模拟数据
        test_result = {
            "success": True,
            "type": "tweet",
            "content": {
                "text": "这是一条测试推文",
                "author": "测试用户",
                "username": "testuser",
                "created_at": "2024-01-01 12:00:00",
                "likes": 100,
                "retweets": 50,
                "views": 1000,
                "replies": 10,
                "media": []
            }
        }

        markdown = fetch_x.generate_markdown(test_result, "123456", "testuser", "https://x.com/testuser/status/123456")

        if "测试用户" in markdown and "100" in markdown and "这是一条测试推文" in markdown:
            print("✅ Markdown 生成正常")
            return True
        else:
            print("❌ Markdown 生成失败")
            print(markdown)
            return False
    except Exception as e:
        print(f"❌ Markdown 生成测试失败: {e}")
        return False

def main():
    print("=" * 50)
    print("  X Fetcher Skill 功能测试")
    print("=" * 50)

    tests = [
        test_import,
        test_config,
        test_fetch_x,
        test_directory_creation,
        test_markdown_generation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("  测试总结")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！Skill 已准备就绪。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖。")
        print("\n故障排除:")
        print("1. 安装依赖: pip3 install -r scripts/requirements.txt")
        print("2. 运行配置: bash scripts/quick-start.sh")
        print("3. 查看文档: cat USAGE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
