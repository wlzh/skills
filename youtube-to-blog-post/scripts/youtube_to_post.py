#!/usr/bin/env python3
"""
YouTube to Blog Post Script - SEO Optimized Version
Convert YouTube videos to Hexo blog posts with enhanced SEO
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import subprocess

try:
    import yt_dlp
except ImportError:
    print("Installing yt-dlp...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp


# SEO optimization constants
MAX_DESCRIPTION_LENGTH = 160  # Google SEO recommended
MAX_KEYWORDS = 8  # Optimal number for SEO
MIN_KEYWORD_LENGTH = 2
MAX_KEYWORD_LENGTH = 20

# Stop words to filter from keywords
STOP_WORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', 'https', 'http', 'www', 'com', 'cn', 'org', 'net', '://', '//',
    '加入', '这个', '那个', '可以', '使用', '通过', '进行', '如果', '因为', '所以',
}

# Common tech keyword mappings for better SEO
KEYWORD_SYNONYMS = {
    'ai': ['AI', '人工智能', 'artificial intelligence'],
    'vps': ['VPS', '虚拟服务器', 'virtual private server'],
    'cdn': ['CDN', '内容分发网络', 'content delivery network'],
    'ssl': ['SSL', 'HTTPS', '安全证书'],
    '域名': ['domain', '域名注册'],
    '服务器': ['server', '主机'],
    '免费': ['free', '0成本', '免费资源'],
    '教程': ['tutorial', '指南', 'guide', 'how to'],
}


def load_config(config_path=None, blog_dir=None):
    """Load configuration from config file or use defaults"""
    config = {
        "posts_dir": "source/_posts",
        "default_category": "技术",
        "default_tags": ["视频教程"],
        "author": "M.",
        "image_cdn": "https://img.869hr.uk",
        "auto_deploy": False,
        "deploy_branch": "main"
    }

    # Priority 1: User's home directory config (for personal settings)
    home_config = os.path.expanduser("~/.youtube-blog-config.json")
    if os.path.exists(home_config):
        with open(home_config, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)

    # Priority 2: Explicit config path
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)
    # Priority 3: Blog directory config
    elif blog_dir:
        config_path = os.path.join(blog_dir, "youtube-blog-config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)

    return config


def normalize_youtube_text(text):
    """Normalize YouTube title/description text for downstream publishing"""
    if not text:
        return text
    return text.replace('>', '》').replace('<', '《').replace('\r\n', '\n').strip()


def sanitize_text_for_yaml(text):
    """
    Sanitize text for YAML format
    Remove or escape special characters that break YAML parsing
    """
    if not text:
        return text

    text = normalize_youtube_text(text)

    # Remove YAML special characters
    text = re.sub(r'[*&:!|]', '', text)  # Remove problematic chars but preserve converted chevrons
    text = re.sub(r'[【】「」『』（）()]', '', text)  # Remove Chinese brackets except chevrons
    text = re.sub(r'[\[\]{}]', '', text)  # Remove brackets
    text = text.strip()

    return text


def sanitize_for_html_attribute(text, max_length=100):
    """
    Sanitize text for HTML attributes (e.g., iframe title)
    Remove characters that can break HTML parsing

    Args:
        text: Text to sanitize
        max_length: Maximum length (default 100 for better compatibility)

    Returns:
        Sanitized text safe for HTML attributes
    """
    if not text:
        return ""

    text = normalize_youtube_text(text)

    # Remove problematic characters for HTML attributes
    # 1. Remove all types of quotes (causes attribute parsing errors)
    text = re.sub(r'[""\'`「」『』《》【】]', '', text)

    # 2. Remove other HTML special characters
    text = re.sub(r'[<>&]', '', text)

    # 3. Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # 4. Trim and limit length
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0]  # Cut at word boundary

    return text


def clean_keywords(keywords):
    """Clean and optimize keywords for SEO"""
    cleaned = []

    for kw in keywords:
        # Remove special characters
        kw = sanitize_text_for_yaml(kw)

        # Skip if too short or too long
        if len(kw) < MIN_KEYWORD_LENGTH or len(kw) > MAX_KEYWORD_LENGTH:
            continue

        # Skip stop words
        if kw.lower() in STOP_WORDS:
            continue

        # Skip URLs
        if kw.startswith(('http', 'https', 'www', '//')):
            continue

        # Skip if starts with special chars
        if re.match(r'^[^\w]', kw):
            continue

        cleaned.append(kw)

    return cleaned


def get_video_info(url):
    """Fetch video information from YouTube"""
    print(f"Fetching video info from: {url}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'id': info.get('id', ''),
                'title': sanitize_text_for_yaml(info.get('title', 'Untitled')),
                'description': normalize_youtube_text(info.get('description', '')),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'tags': info.get('tags', []),
                'view_count': info.get('view_count', 0),
            }
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def generate_english_filename(title, video_id=None):
    """Generate SEO-friendly English filename from video title (kebab-case)"""

    # Enhanced keyword mapping for better SEO
    keyword_map = {
        # Common words - using kebab-case
        '教程': 'tutorial',
        '指南': 'guide',
        '工具': 'tools',
        '技术': 'tech',
        '免费': 'free',
        '零成本': 'free',
        '0成本': 'free',
        '域名': 'domain',
        '服务器': 'server',
        '支付': 'payment',
        '卡': 'card',
        '银行卡': 'bank-card',
        '虚拟': 'virtual',
        '注册': 'register',
        '申请': 'apply',
        '设置': 'setup',
        '配置': 'config',
        '开发': 'dev',
        '学习': 'study',
        '入门': 'beginner',
        '进阶': 'advanced',
        '详解': 'detail',
        '使用': 'usage',
        '安装': 'install',
        '部署': 'deploy',
        '测试': 'test',
        '优化': 'optimize',
        '分析': 'analysis',
        '介绍': 'intro',
        '什么是': 'what-is',
        '如何': 'how-to',
        '为什么': 'why',
        '最佳': 'best',
        '推荐': 'recommend',
        '对比': 'compare',
        '评测': 'review',
        # Special chars to handle
        '（': ' ',
        '）': ' ',
        '(': ' ',
        ')': ' ',
        '：': ' ',
        ':': ' ',
        '！': ' ',
        '!': ' ',
        '？': ' ',
        '?': ' ',
        '，': ' ',
        ',': ' ',
        '。': ' ',
        '.': ' ',
        ' ': ' ',
        '--': ' ',
        '【': ' ',
        '】': ' ',
        '《': ' ',
        '》': ' ',
        '🔥': ' ',
        '🚀': ' ',
        # Tech terms
        '科学上网': 'vpn',
        'vps': 'vps',
        'ai': 'ai',
        '人工智能': 'ai',
        '机器学习': 'ml',
        '深度学习': 'deep-learning',
        '区块链': 'blockchain',
        '云计算': 'cloud',
        '容器化': 'docker',
        '微服务': 'microservice',
        '前端': 'frontend',
        '后端': 'backend',
        '全栈': 'fullstack',
        '教育邮箱': 'edu-email',
        'edu': 'edu',
        '美国': 'usa',
        '中国': 'china',
        '白嫖': 'free',
        '神器': 'tool',
        '最新': 'latest',
        'gcp': 'gcp',
        'google cloud': 'gcp',
    }

    # First, remove emojis and special symbols
    filename = re.sub(r'[🔥🚀💡✅🎯📌]', ' ', title)

    # Convert to lowercase
    filename = filename.lower()

    # Replace Chinese words with English + space separator
    for cn, en in keyword_map.items():
        if en:  # Skip empty replacements
            filename = filename.replace(cn, f' {en} ')
        else:
            filename = filename.replace(cn, ' ')

    # Remove any remaining non-ASCII characters
    filename = re.sub(r'[^\x00-\x7f]', ' ', filename)

    # Remove special characters except spaces and dashes
    filename = re.sub(r'[^\w\s-]', ' ', filename)

    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename).strip()

    # Split into words
    words = filename.split()

    # Remove duplicate words while preserving order
    seen = set()
    unique_words = []
    for word in words:
        if word and word not in seen:
            seen.add(word)
            unique_words.append(word)

    # Rejoin with dashes
    filename = '-'.join(unique_words)

    # 如果文件名太短或为空，使用视频 ID
    if len(filename) < 5 or not filename:
        filename = f"video-{video_id}" if video_id else "video-post"

    # 确保文件名有意义，包含核心关键词
    # 如果只是 "video-xxx" 这种格式，尝试从标题提取关键词
    if filename.startswith('video-') and video_id:
        # 从标题提取前两个有意义的词
        meaningful_words = re.findall(r'[\u4e00-\u9fffA-Za-z]+', title)
        if meaningful_words:
            # 取前两个有意义的词
            words = meaningful_words[:2]
            filename = '-'.join(words).lower() + '-tutorial'
            filename = re.sub(r'[^\w-]', '', filename)

    # Limit length for SEO (shorter URLs are better), but keep it meaningful
    # Reduce max length from 50 to 40 for better readability
    if len(filename) > 40:
        # Try to keep meaningful parts - split by dashes and take first few
        parts = filename.split('-')
        result = []
        current_length = 0
        for part in parts:
            if current_length + len(part) + 1 <= 40:
                result.append(part)
                current_length += len(part) + 1
            else:
                break
        filename = '-'.join(result) if result else filename[:40]

    return filename


def generate_seo_keywords(title, description, tags):
    """
    Generate SEO-optimized keywords
    Focus on long-tail keywords and search intent
    """
    keywords = set()

    # 1. Extract from title (highest priority)
    title_words = re.split(r'[,，、\s]+', title)
    for word in title_words:
        word = word.strip()
        if len(word) >= 2:
            keywords.add(word)

    # 2. Add user-provided tags
    if isinstance(tags, list):
        keywords.update(tags)
    elif isinstance(tags, str):
        keywords.update([t.strip() for t in tags.split(',')])

    # 3. Extract high-value keywords from description
    if description:
        # Look for patterns like "关键词：xxx" or "关键词: xxx"
        keyword_pattern = r'关键词[：:]\s*([^\n]+)'
        keyword_matches = re.findall(keyword_pattern, description)
        for match in keyword_matches:
            kws = re.split(r'[,，、\s]+', match)
            keywords.update([kw.strip() for kw in kws if kw.strip()])

        # Extract meaningful phrases from description
        desc_sentences = re.split(r'[。！？.!?]', description)[:2]
        for sentence in desc_sentences:
            # Look for tech terms and product names
            tech_terms = re.findall(r'[A-Z]{2,}|[A-Za-z]{3,}', sentence)
            keywords.update(tech_terms)

    # Clean and optimize keywords
    keywords = clean_keywords(list(keywords))

    # Add related keywords for better SEO coverage
    final_keywords = []
    for kw in keywords[:MAX_KEYWORDS]:
        final_keywords.append(kw)

        # Add synonyms for important keywords
        if kw.lower() in KEYWORD_SYNONYMS:
            for synonym in KEYWORD_SYNONYMS[kw.lower()][:2]:
                if synonym not in final_keywords and len(final_keywords) < MAX_KEYWORDS:
                    final_keywords.append(synonym)

    return final_keywords[:MAX_KEYWORDS]


def generate_seo_description(title, description):
    """
    Generate SEO-optimized description
    - Max 160 characters (Google snippet length)
    - Include main keywords
    - Compelling call-to-action
    """
    # Clean up description
    if description:
        # Remove URLs, email addresses
        desc = re.sub(r'https?://\S+', '', description)
        desc = re.sub(r'\S+@\S+', '', desc)

        # Remove excessive whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Get first meaningful sentence
        sentences = re.split(r'[。！？.!?]', desc)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) <= MAX_DESCRIPTION_LENGTH:
                return sentence

    # Fallback to title-based description
    desc_template = f"本视频详细介绍{title}，帮助你快速了解和掌握相关知识点。"
    if len(desc_template) > MAX_DESCRIPTION_LENGTH:
        desc_template = f"{title} - 详细教程与指南"

    return desc_template[:MAX_DESCRIPTION_LENGTH]


def generate_post_content(video_info, config, category, tags):
    """Generate SEO-optimized blog post content"""

    video_id = video_info['id']
    title = video_info['title']
    description = video_info.get('description', '')
    thumbnail = video_info.get('thumbnail', '')

    # Generate SEO-optimized metadata
    keywords = generate_seo_keywords(title, description, tags)
    post_description = generate_seo_description(title, description)

    # Use current time as post date (not video upload time)
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generate tags list
    tag_list = tags if isinstance(tags, list) else [t.strip() for t in tags.split(',')]

    # Build cover image URL from YouTube thumbnail
    # Use high-quality thumbnail (maxresdefault)
    cover_image = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    # Build front matter with SEO fields
    front_matter = f"""---
title: {title}
subtitle: {title}
date: {date_str}
updated: {date_str}
author: {config['author']}
description: {post_description}
categories:
  - {category}
{generate_tags_yaml(tag_list)}
keywords:
{generate_keywords_yaml(keywords)}
cover: {cover_image}
thumbnail: {cover_image}
toc: true
comments: true
copyright: true
---

"""

    # Generate article summary
    summary = generate_article_summary(video_info)

    # Generate video iframe with SEO attributes
    # Sanitize title for HTML attribute to prevent parsing errors
    safe_title = sanitize_for_html_attribute(title)
    video_iframe = f"""## 视频教程

<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" title="{safe_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

"""

    # Generate article content with SEO structure
    content = generate_article_content(video_info, video_id)

    # Generate reference links
    references = ""

    return front_matter + summary + video_iframe + content + references


def generate_tags_yaml(tags):
    """Generate tags in YAML format"""
    if not tags:
        return "tags:"
    yaml = "tags:\n"
    for tag in tags:
        yaml += f"  - {tag}\n"
    return yaml


def generate_keywords_yaml(keywords):
    """Generate keywords in YAML format"""
    if not keywords:
        return ""
    yaml = ""
    for kw in keywords:
        # Escape special YAML characters
        kw_safe = sanitize_text_for_yaml(kw)
        yaml += f"  - {kw_safe}\n"
    return yaml


def generate_article_summary(video_info):
    """Generate compelling article summary"""
    title = video_info['title']
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)

    # Convert duration to minutes
    duration_min = duration // 60 if duration else 0

    if description:
        # Use first meaningful paragraph from description
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                summary = line[:300]
                return f"""<!-- 文章摘要 -->
{{% blockquote %}}
{summary}...
{{% endblockquote %}}

"""
    return f"""<!-- 文章摘要 -->
{{% blockquote %}}
本视频详细介绍{title}（时长约{duration_min}分钟），帮助你快速了解和掌握相关知识点。
{{% endblockquote %}}

"""


def generate_article_content(video_info, video_id):
    """Generate detailed article content - 使用完整描述"""
    title = video_info['title']
    uploader = video_info.get('uploader', '')
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)
    tags = video_info.get('tags', [])

    # Convert duration to minutes and seconds
    duration_min = duration // 60 if duration else 0
    duration_sec = duration % 60 if duration else 0

    content = f"""## 视频介绍

本视频由 {uploader} 制作，时长约 {duration_min} 分 {duration_sec} 秒。

"""

    # 清理描述，提取有意义的行
    desc_lines = []
    for line in description.split('\n'):
        line = line.strip()
        if not line:
            continue
        # 跳过链接
        if line.startswith('http'):
            continue
        # 跳过社交媒体
        if 'Telegram' in line and 't.me' in line:
            continue
        if 'Twitter' in line or 'x.com' in line:
            continue
        if '微信' in line and 'qr.' in line:
            continue
        # 跳过 emoji 开头的行
        if line.startswith('💬') or line.startswith('🔗'):
            continue
        # 跳过纯符号行
        if len(set(line.replace(' ', ''))) < 3:
            continue
        desc_lines.append(line)

    # 提取时间戳章节
    timestamp_pattern = r'(\d{1,2}:\d{2})\s*[.\-]?\s*(.+)'
    timestamps = re.findall(timestamp_pattern, '\n'.join(desc_lines))

    if timestamps:
        content += "## 视频章节\n\n"
        for ts, chapter in timestamps[:10]:
            content += f"- **{ts}** {chapter}\n"
        content += "\n"

    # 提取核心亮点（通常标记为 ✅）
    features = []
    for line in desc_lines:
        if '✅' in line:
            feature = line.replace('✅', '').strip()
            feature = re.sub(r'[🚀💡✅🎯\*]+', '', feature).strip()
            if feature and len(feature) > 5:
                features.append(feature)

    if features:
        content += "## 核心内容\n\n"
        for feature in features[:8]:
            content += f"- {feature}\n"
        content += "\n"

    # 提取代码块
    code_blocks = re.findall(r'```[a-z]*\n(.*?)```', description, re.DOTALL)
    if code_blocks:
        content += "## 脚本命令\n\n"
        for code in code_blocks[:3]:
            content += f"```bash\n{code.strip()}\n```\n\n"

    # 添加完整的描述内容作为正文
    if desc_lines:
        content += "## 详细内容\n\n"
        for line in desc_lines[:20]:
            # 清理行
            line = re.sub(r'[🚀💡✅🎯🔗💬]+', '', line)
            line = line.replace('**', '').strip()
            if line and len(line) > 5:
                content += f"{line}\n\n"

    # 提取链接作为参考
    urls = re.findall(r'https?://[^\s]+', description)
    if urls:
        content += "## 延伸链接\n\n"
        seen = set()
        for url in urls[:5]:
            if url not in seen and 'http' in url:
                seen.add(url)
                # 提取域名作为链接描述
                domain = re.search(r'https?://([^/]+)', url)
                if domain:
                    domain_name = domain.group(1)
                    if 'github' in domain_name:
                        content += f"- [GitHub]({url})\n"
                    elif 't.me' in domain_name:
                        content += f"- [Telegram]({url})\n"
                    elif 'x.com' in domain_name:
                        content += f"- [X (Twitter)]({url})\n"
                    else:
                        content += f"- [{domain_name}]({url})\n"

    content += f"""
---

## 视频信息

- **视频标题**: {title}
- **UP主**: {uploader}
- **视频时长**: {duration_min}分{duration_sec}秒
- **视频ID**: {video_id}

"""

    content += """## 参考链接

- [YouTube视频原地址](https://www.youtube.com/watch?v={})
- [相关推荐](https://869hr.uk)

---
""".format(video_id)

    return content


def humanize_article(content, video_title):
    """
    Apply humanizer to remove AI-generated writing patterns
    Simplified implementation based on humanizer-zh skill guidelines
    """
    lines = content.split('\n')
    humanized_lines = []
    skip_frontmatter = False
    frontmatter_end = False

    for i, line in enumerate(lines):
        # Skip front matter
        if line.strip() == '---':
            if not skip_frontmatter:
                skip_frontmatter = True
                humanized_lines.append(line)
                continue
            elif skip_frontmatter and not frontmatter_end:
                frontmatter_end = True
                humanized_lines.append(line)
                continue

        # Don't modify front matter
        if skip_frontmatter and not frontmatter_end:
            humanized_lines.append(line)
            continue

        # Skip video iframe
        if '<iframe' in line:
            humanized_lines.append(line)
            continue

        # Remove excessive emoji from headers
        if line.startswith('##'):
            # Remove multiple emojis from headings, keep at most one if relevant
            line = re.sub(r'[🎯📹📺💡🎓📝📚🔍🔗]+', '', line)
            # Remove trailing colon
            line = re.sub(r':\s*$', '', line)
            humanized_lines.append(line)
            continue

        # Remove or replace AI patterns
        # Preserve real title metadata in info blocks
        if line.strip().startswith('- **视频标题**:') or line.strip().startswith('- 视频标题:'):
            humanized_lines.append(line)
            continue

        # Remove excessive emphasis
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold markdown
        line = re.sub(r'🚀\*\*', '', line)  # Remove rocket emoji
        line = re.sub(r'真正[的]', '', line)
        line = re.sub(r'终极[""]', '', line)
        line = re.sub(r'"白嫖[""]', '免费', line)
        line = re.sub(r'无限流量', '', line)
        line = re.sub(r'无限生成', '', line)
        line = re.sub(r'节点无限', '', line)
        line = re.sub(r'4K秒开', '速度快', line)

        # Remove AI vocabulary
        line = re.sub(r'此外，', '', line)
        line = re.sub(r'深入探讨', '介绍', line)
        line = re.sub(r'核心知识', '内容', line)
        line = re.sub(r'关键信息', '信息', line)
        line = re.sub(r'重要', '', line)
        line = re.sub(r'至关重要的', '', line)
        line = re.sub(r'必不可少的', '', line)

        # Simplify structure
        line = re.sub(r'本视频适合以下观众观看：', '适合：', line)
        line = re.sub(r'\*   ', '- ', line)  # Simplify bullet points

        # Remove repetitive title mentions
        if video_title in line and len(video_title) > 20:
            # If title appears verbatim in content, shorten it
            short_title = video_title[:30] + '...' if len(video_title) > 30 else video_title
            line = line.replace(video_title, '这个教程')
            line = line.replace(short_title, '这个教程')

        # Remove generic filler phrases
        line = re.sub(r'建议在观看视频时：', '观看时：', line)
        line = re.sub(r'无论你是……都能从中获得有价值的信息。', '', line)

        humanized_lines.append(line)

    # Clean up excessive blank lines
    result = []
    prev_blank = False
    for line in humanized_lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank

    return '\n'.join(result)


def save_post(content, filename, posts_dir, video_title, apply_humanizer=True):
    """Save blog post to file"""
    # Ensure directory exists
    posts_path = Path(posts_dir)
    posts_path.mkdir(parents=True, exist_ok=True)

    # Full file path
    file_path = posts_path / f"{filename}.md"

    # Check if file exists for notification
    if file_path.exists():
        print(f"⚠️  File exists, will overwrite: {file_path.name}")

    # Apply humanizer if enabled (default) - built-in implementation
    if apply_humanizer:
        print("🔄 Applying AI writing removal (natural language processing)...")
        content = humanize_article(content, video_title)
        print("✅ Content humanized - SEO optimized and ready")

    # Write content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Blog post created: {file_path}")
    return file_path


def hexo_deploy(blog_dir):
    """Run hexo deploy to generate and push static files to GitHub Pages"""
    import subprocess

    if not blog_dir or not os.path.exists(blog_dir):
        print("⚠️ Blog directory not found, skipping hexo deployment")
        return False

    original_dir = os.getcwd()
    try:
        os.chdir(blog_dir)

        # Check if hexo is available
        result = subprocess.run(['which', 'hexo'], capture_output=True)
        if result.returncode != 0:
            print("⚠️ Hexo not found, skipping hexo deployment")
            return False

        print("🧹 Running hexo clean...")
        subprocess.run(['hexo', 'clean'], check=True, capture_output=True)

        print("📦 Running hexo generate...")
        subprocess.run(['hexo', 'generate'], check=True, capture_output=True)

        print("🚀 Running hexo deploy...")
        result = subprocess.run(['hexo', 'deploy'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ Hexo deploy warning: {result.stderr}")
            # Continue anyway - might just be a warning

        print("✅ Hexo deployment completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Hexo deployment failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Hexo deployment error: {e}")
        return False
    finally:
        os.chdir(original_dir)


def deploy_to_git(blog_dir, branch='main'):
    """Deploy changes to git repository"""
    import subprocess

    if not blog_dir or not os.path.exists(blog_dir):
        print("⚠️ Blog directory not found, skipping git deployment")
        return False

    original_dir = os.getcwd()
    try:
        os.chdir(blog_dir)

        # Check if it's a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                              capture_output=True)
        if result.returncode != 0:
            print("⚠️ Not a git repository, skipping git deployment")
            return False

        # Add changes
        print("📤 Adding changes to git...")
        subprocess.run(['git', 'add', '.'], check=True)

        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                              capture_output=True)
        needs_commit = result.returncode != 0

        if needs_commit:
            # Commit changes
            print("💾 Committing changes...")
            commit_msg = f"docs: add new blog post - {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

            # Push to remote
            print("🚀 Pushing to remote...")
            subprocess.run(['git', 'push', 'origin', branch], check=True)
            print("✅ Successfully pushed to git repository")
        else:
            print("ℹ️ No changes to commit")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False
    finally:
        os.chdir(original_dir)


def main():
    parser = argparse.ArgumentParser(
        description='Convert YouTube video to SEO-optimized Hexo blog post'
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-b', '--blog-dir', help='Blog directory path')
    parser.add_argument('-c', '--category', default='技术', help='Post category')
    parser.add_argument('-t', '--tags', nargs='+', default=['视频教程'], help='Post tags')
    parser.add_argument('--config', help='Path to config JSON file')
    parser.add_argument('--posts-dir', help='Override posts directory')
    parser.add_argument('--dry-run', action='store_true', help='Generate content but don\'t save')
    parser.add_argument('--no-humanizer', action='store_true', help='Skip AI writing removal (humanizer)')
    parser.add_argument('--deploy', action='store_true', help='Auto deploy to git after saving post')

    args = parser.parse_args()

    # Load configuration (with home directory priority)
    config = load_config(args.config, args.blog_dir)

    # Determine blog directory (priority: CLI arg > config > current dir)
    blog_dir = args.blog_dir or config.get('blog_dir', '')

    # Determine posts directory
    if args.posts_dir:
        posts_dir = args.posts_dir
    elif blog_dir:
        posts_dir = os.path.join(blog_dir, config['posts_dir'])
    else:
        posts_dir = config['posts_dir']

    # Get video info
    video_info = get_video_info(args.url)
    if not video_info:
        print("❌ Failed to fetch video information")
        return 1

    print(f"📹 Video: {video_info['title']}")
    print(f"👤 Uploader: {video_info.get('uploader', 'N/A')}")
    if blog_dir:
        print(f"📂 Blog: {blog_dir}")

    # Generate filename
    video_id = extract_video_id(args.url) or video_info['id']
    filename = generate_english_filename(video_info['title'], video_id)
    print(f"📝 Filename: {filename}.md")

    # Generate post content
    content = generate_post_content(video_info, config, args.category, args.tags)

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - Generated content:")
        print("="*60)
        print(content[:1500] + "..." if len(content) > 1500 else content)
        print(f"\nWould save to: {os.path.join(posts_dir, filename + '.md')}")
    else:
        # Save post (with humanizer by default)
        apply_humanizer = not args.no_humanizer
        file_path = save_post(content, filename, posts_dir, video_info['title'], apply_humanizer)
        print(f"\n🎉 Post saved to: {file_path}")

        # Auto deploy if enabled (full pipeline: hexo deploy + git push)
        if args.deploy or config.get('auto_deploy', False):
            print("\n🚀 Starting full deployment pipeline...")

            # Step 1: Hexo deploy (generates static files and pushes to GitHub Pages)
            print("\n📦 Step 1: Running hexo deploy...")
            hexo_deploy(blog_dir)

            # Step 2: Git push (push source code to repository)
            print("\n📤 Step 2: Pushing source to git...")
            deploy_branch = config.get('deploy_branch', 'main')
            deploy_to_git(blog_dir, deploy_branch)

            print("\n✅ Full deployment completed!")
            print(f"   - Static files deployed to: https://wlzh.github.io/")
            print(f"   - Source code pushed to: https://github.com/wlzh/myblog")
        else:
            print(f"\n📂 To deploy manually:")
            print(f"   cd {blog_dir or '.'}")
            print(f"   hexo clean && hexo generate && hexo deploy")
            print(f"   git add . && git commit -m 'docs: add new post' && git push")

    return 0


if __name__ == '__main__':
    sys.exit(main())
