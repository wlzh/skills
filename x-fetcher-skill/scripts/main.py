#!/usr/bin/env python3
"""
X Fetcher - Skill 封装脚本
支持配置文件和自动保存功能
"""

import sys
import os
import json
import re
import yaml
import requests
from pathlib import Path
from urllib.parse import urlparse

# 添加父目录到路径以便导入 fetch_x
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_x

def load_config():
    """加载配置文件"""
    # 优先级：项目级 > 用户级
    config_paths = [
        Path.cwd() / ".x-fetcher" / "EXTEND.md",
        Path.home() / ".x-fetcher" / "EXTEND.md"
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析 YAML frontmatter
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            config_yaml = parts[1].strip()
                            config = yaml.safe_load(config_yaml)
                            return config
                    # 如果没有 frontmatter，尝试解析整个文件
                    config = yaml.safe_load(content)
                    return config
            except Exception as e:
                print(f"⚠️  配置文件解析错误: {e}", file=sys.stderr)

    return None

def get_default_output_dir(config):
    """获取默认输出目录"""
    if config and 'default_output_dir' in config:
        output_dir = config['default_output_dir']
        # 展开用户目录
        output_dir = os.path.expanduser(output_dir)
        return output_dir
    return None

def ensure_output_dir(output_dir, username):
    """确保输出目录存在"""
    if output_dir:
        # 如果指定了完整路径，使用它
        full_path = Path(output_dir)
    else:
        # 使用默认路径
        full_path = Path.cwd() / "x-fetcher"

    # 添加 username 子目录
    if username:
        full_path = full_path / username

    # 创建目录
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path

def download_media_files(media_urls, output_dir, tweet_id):
    """下载媒体文件到本地"""
    if not media_urls:
        return {}

    # 创建媒体目录
    media_dir = Path(output_dir)
    imgs_dir = media_dir / "imgs"
    videos_dir = media_dir / "videos"
    imgs_dir.mkdir(exist_ok=True)
    videos_dir.mkdir(exist_ok=True)

    downloaded = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for i, url in enumerate(media_urls, 1):
        try:
            # 判断是图片还是视频
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov', '.webm', 'video'])

            # 获取文件扩展名
            parsed = urlparse(url)
            ext = Path(parsed.path).suffix or ('.mp4' if is_video else '.jpg')

            # 生成文件名
            if is_video:
                filename = f"{tweet_id}_video{i}{ext}"
                filepath = videos_dir / filename
            else:
                filename = f"{tweet_id}_img{i}{ext}"
                filepath = imgs_dir / filename

            # 下载文件
            print(f"  📥 正在下载: {filename}", file=sys.stderr)
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            # 记录映射关系（相对路径）
            if is_video:
                downloaded[url] = f"videos/{filename}"
            else:
                downloaded[url] = f"imgs/{filename}"

            print(f"  ✅ 已下载: {filename}", file=sys.stderr)

        except Exception as e:
            print(f"  ⚠️  下载失败: {url} - {e}", file=sys.stderr)

    return downloaded

def update_markdown_media_links(markdown_content, url_mapping):
    """更新 Markdown 中的媒体链接为本地路径"""
    if not url_mapping:
        return markdown_content

    updated = markdown_content
    for remote_url, local_path in url_mapping.items():
        # 替换所有出现的远程 URL
        updated = updated.replace(remote_url, local_path)

    return updated

def save_markdown_to_dir(markdown_content, tweet_id, username, output_dir):
    """保存 Markdown 文件到指定目录"""
    from datetime import datetime

    # 确保输出目录存在
    dir_path = ensure_output_dir(output_dir, username)

    # 生成文件名
    filename = f"{tweet_id}.md"
    filepath = dir_path / filename

    # 保存文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return str(filepath)

def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <x_url> [选项]")
        print("选项:")
        print("  --output <path>      输出目录或文件路径")
        print("  --download-media     下载媒体文件到本地")
        print("  --json               JSON 输出（不保存 Markdown）")
        print("  --no-save            不保存 Markdown 文件")
        print("  --check-config       检查配置文件")
        sys.exit(1)

    # 检查是否只是查看配置
    if '--check-config' in sys.argv:
        config = load_config()
        if config:
            print("✅ 配置文件已找到:")
            print(json.dumps(config, ensure_ascii=False, indent=2))
        else:
            print("❌ 未找到配置文件")
            print("配置文件位置（优先级）:")
            print(f"  1. {Path.cwd() / '.x-fetcher' / 'EXTEND.md'}")
            print(f"  2. {Path.home() / '.x-fetcher' / 'EXTEND.md'}")
        sys.exit(0)

    # 解析参数
    url = None
    output_path = None
    download_media = '--download-media' in sys.argv
    json_output = '--json' in sys.argv
    no_save = '--no-save' in sys.argv

    # 解析位置参数和选项
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--output' and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif arg in ['--download-media', '--json', '--no-save']:
            i += 1
        else:
            if not arg.startswith('--') and url is None:
                url = arg
            i += 1

    if not url:
        print("❌ 错误: 未提供 URL", file=sys.stderr)
        sys.exit(1)

    # 加载配置
    config = load_config()

    # 如果没有配置文件，提示需要配置
    if not config:
        print("⚠️  未找到配置文件", file=sys.stderr)
        print("请先设置默认下载目录。", file=sys.stderr)
        print("", file=sys.stderr)
        print("配置文件位置（选择其一）:", file=sys.stderr)
        print(f"  1. {Path.cwd() / '.x-fetcher' / 'EXTEND.md'} （项目级）", file=sys.stderr)
        print(f"  2. {Path.home() / '.x-fetcher' / 'EXTEND.md'} （用户级）", file=sys.stderr)
        print("", file=sys.stderr)
        print("配置文件内容示例:", file=sys.stderr)
        print("---", file=sys.stderr)
        print("default_output_dir: ~/Downloads/x-fetcher", file=sys.stderr)
        print("auto_save: true", file=sys.stderr)
        print("download_media: ask", file=sys.stderr)
        print("---", file=sys.stderr)
        sys.exit(1)

    # 获取默认输出目录
    if not output_path:
        output_path = get_default_output_dir(config)

    # 获取 auto_save 配置
    auto_save = config.get('auto_save', True)
    if no_save:
        auto_save = False

    # 获取 download_media 配置
    download_media_config = config.get('download_media', 'ask')
    should_download_media = False

    # 如果命令行指定了 --download-media，强制下载
    if download_media:
        should_download_media = True
    elif download_media_config == True or download_media_config == 'true':
        should_download_media = True
    elif download_media_config == False or download_media_config == 'false':
        should_download_media = False
    # 'ask' 模式会在后面处理

    # 调用原始的 fetch_tweet 函数
    result, tweet_id, username = fetch_x.fetch_tweet(url)

    # 输出 JSON 结果
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 输出 JSON 到 stderr，便于调试
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)

    # 如果抓取成功，保存 Markdown
    if result.get("success") and auto_save and not json_output:
        try:
            markdown_content = fetch_x.generate_markdown(result, tweet_id, username, url)

            # 获取媒体 URL
            content = result.get('content', {})
            media_urls = content.get('media', [])

            # 确定输出目录
            dir_path = ensure_output_dir(output_path, username)

            # 处理媒体文件下载
            if media_urls:
                if download_media_config == 'ask' and not download_media:
                    # 询问用户是否下载
                    print(f"\n📎 发现 {len(media_urls)} 个媒体文件", file=sys.stderr)
                    response = input("是否下载媒体文件到本地？(y/n): ").strip().lower()
                    should_download_media = response in ['y', 'yes', '是']

                if should_download_media:
                    print(f"\n📥 开始下载媒体文件...", file=sys.stderr)
                    url_mapping = download_media_files(media_urls, str(dir_path), tweet_id)
                    if url_mapping:
                        markdown_content = update_markdown_media_links(markdown_content, url_mapping)
                        print(f"✅ 已下载 {len(url_mapping)} 个媒体文件", file=sys.stderr)

            # 保存 Markdown 文件
            filepath = save_markdown_to_dir(markdown_content, tweet_id, username, output_path)
            print(f"\n✅ Markdown 已保存到: {filepath}", file=sys.stderr)

            if media_urls and not should_download_media and download_media_config != 'false':
                print(f"💡 提示: 媒体文件保留为远程 URL", file=sys.stderr)

        except Exception as e:
            print(f"\n❌ 保存 Markdown 失败: {e}", file=sys.stderr)
    elif not auto_save and not json_output:
        print("\nℹ️  自动保存已禁用", file=sys.stderr)

if __name__ == "__main__":
    main()
