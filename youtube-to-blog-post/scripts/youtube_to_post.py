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

# Standard tag taxonomy (v3.2) - must be used when generating tags
STANDARD_TAGS = {
    'AI': ['AI', '人工智能', 'AGI', 'ai'],
    'AI工具': ['AI工具', 'ai工具', 'ai tools'],
    'AI前沿': ['AI前沿', 'ai前沿', 'AI frontier'],
    'LLM': ['LLM', '大语言模型', 'llm'],
    'DeepSeek': ['DeepSeek', 'deepseek'],
    'ChatGPT': ['ChatGPT', 'chatgpt', 'GPT'],
    'Claude': ['Claude'],
    'Skills': ['Skills', 'skills'],
    '跨境支付': ['跨境支付', '支付', '出海收款'],
    '信用卡': ['信用卡', '虚拟信用卡', 'credit card'],
    'Wise': ['Wise', 'wise'],
    'Stripe': ['Stripe', 'stripe'],
    '苹果支付': ['苹果支付', 'iOS支付', 'apple payment'],
    '加密货币': ['加密货币', 'crypto', '比特币', '币安'],
    'VPN': ['VPN', 'vpn', '梯子', '翻墙', '科学上网', 'v2ray'],
    'VPS': ['VPS', 'vps', '服务器', '云服务器'],
    'Cloudflare': ['Cloudflare', 'cloudflare', 'CF'],
    '网络工具': ['网络工具', 'network tools'],
    '网络安全': ['网络安全', 'network security'],
    'ip属性': ['ip属性', 'ip检查', 'IP属性'],
    'eSIM': ['eSIM', 'esim'],
    'Apple ID': ['Apple ID', 'apple id', '苹果账号', '美区账号'],
    'App Store': ['App Store', 'app store'],
    'iOS': ['iOS', 'ios'],
    '在线工具': ['在线工具', 'online tools'],
    '效率工具': ['效率工具', 'productivity', '自动化'],
    '开发工具': ['开发工具', 'dev tools', '开发者工具'],
    '开源项目': ['开源项目', 'open source', '开源工具'],
    '无需安装': ['无需安装', 'no installation'],
    '剪映': ['剪映', '剪影', '视频编辑'],
    '教程': ['教程', '技术教程', '小白教程', '新手教程'],
    '视频教程': ['视频教程', 'video tutorial'],
    '免费资源': ['免费资源', 'free resource', '白嫖'],
    '学习资源': ['学习资源', 'learning resource'],
    '知识分享': ['知识分享', 'knowledge sharing'],
    '播客推荐': ['播客推荐', 'podcast'],
    '网赚项目': ['网赚项目', 'online earning', '被动收入'],
    '账号注册': ['账号注册', '注册', 'account registration'],
    '账号管理': ['账号管理', 'account management'],
    '邮箱': ['邮箱', 'email', 'gmail'],
    '海外应用': ['海外应用', 'foreign apps'],
    '软件安装': ['软件安装', 'software install'],
    '软件汉化': ['软件汉化', 'i18n', '中文语言包'],
    '本地部署': ['本地部署', 'local deployment', '私有部署'],
    '域名': ['域名', 'domain', '免费域名'],
    '数据安全': ['数据安全', 'data security', '隐私保护', '加密'],
    '文件传输': ['文件传输', 'file transfer', 'PairDrop'],
    '跨平台工具': ['跨平台工具', 'cross platform'],
    '即时通讯': ['即时通讯', 'IM', '即时通信'],
    '社交软件': ['社交软件', 'social'],
    '微信': ['微信', 'wechat'],
    'Telegram': ['Telegram', 'telegram', 'tg'],
    'Google': ['Google', 'google', '谷歌'],
    '闲谈': ['闲谈', 'chat'],
    '技术交流': ['技术交流', 'tech community'],
    '技术支持': ['技术支持', 'tech support'],
    '客户支持': ['客户支持', 'customer support'],
    '故障处理': ['故障处理', 'troubleshooting'],
    '苹果': ['苹果', 'apple', 'iPhone'],
    '公司注册': ['公司注册', 'company registration'],
    '建站': ['建站', 'site building'],
    'SEO': ['SEO', '搜索引擎优化'],
}

def normalize_tag(tag):
    """Normalize a tag to its standard form using the STANDARD_TAGS mapping."""
    tag_stripped = tag.strip()
    for standard, variants in STANDARD_TAGS.items():
        for v in variants:
            if tag_stripped.lower() == v.lower():
                return standard
    return tag_stripped


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


def sanitize_text_for_yaml(text):
    """
    Sanitize text for YAML format
    Remove or escape special characters that break YAML parsing
    """
    if not text:
        return text

    # Remove YAML special characters
    text = re.sub(r'[*&:!|>]', '', text)  # Remove problematic chars
    text = re.sub(r'[【】《》「」『』（）()]', '', text)  # Remove Chinese brackets
    text = re.sub(r'[\[\]{}]', '', text)  # Remove brackets
    text = text.strip()

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
                'description': info.get('description', ''),
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
    """Generate SEO-friendly English filename from video title"""
    # Enhanced keyword mapping for better SEO
    keyword_map = {
        # Common words
        '教程': 'tutorial',
        '指南': 'guide',
        '工具': 'tools',
        '技术': 'tech',
        '免费': 'free',
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
        '的': '',
        '和': 'and',
        '与': 'and',
        '或': 'or',
        '（': '-',
        '）': '',
        '(': '-',
        ')': '',
        '：': '-',
        ':': '-',
        '！': '',
        '!': '',
        '？': '',
        '?': '',
        '，': '-',
        ',': '-',
        '。': '',
        '.': '',
        ' ': '-',
        '--': '-',
        '【': '',
        '】': '',
        '《': '',
        '》': '',
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
    }

    # Replace Chinese and special characters
    filename = title.lower()
    for cn, en in keyword_map.items():
        filename = filename.replace(cn, en)

    # Remove any remaining non-ASCII characters
    filename = re.sub(r'[^\x00-\x7f]', '', filename)
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[\s]+', '-', filename)
    filename = filename.strip('-')

    # If filename is too short or empty, use video ID
    if len(filename) < 5 or not filename:
        filename = f"youtube-{video_id}" if video_id else "video-post"

    # Limit length for SEO (shorter URLs are better)
    if len(filename) > 50:
        filename = filename[:50].rstrip('-')

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

    # Generate tags list - normalize to standard tags
    raw_tags = tags if isinstance(tags, list) else [t.strip() for t in tags.split(',')]
    tag_list = []
    for t in raw_tags:
        normalized = normalize_tag(t)
        if normalized not in tag_list:
            tag_list.append(normalized)

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
    video_iframe = f"""## 视频教程

<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" title="{title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

"""

    # Generate article content with SEO structure
    content = generate_article_content(video_info, video_id)

    # Generate reference links
    references = f"""

## 参考链接

- [YouTube视频原地址](https://www.youtube.com/watch?v={video_id})
- [相关推荐](https://869hr.uk)

---
"""

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
    """Generate SEO-optimized article content"""
    title = video_info['title']
    uploader = video_info.get('uploader', '')
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)
    tags = video_info.get('tags', [])

    # Convert duration to minutes
    duration_min = duration // 60 if duration else 0

    content = f"""## 视频介绍

本视频由 {uploader} 制作，时长约 {duration_min} 分钟。

"""

    # Try to extract meaningful content from description
    # Remove common link lines and emojis
    desc_lines = []
    for line in description.split('\n'):
        line = line.strip()
        # Skip empty lines, links, and common social media lines
        if not line or line.startswith('http') or line.startswith('💬') or line.startswith('🔗'):
            continue
        if 'Telegram' in line and 't.me' in line:
            continue
        if 'Twitter' in line or 'x.com' in line:
            continue
        desc_lines.append(line)

    # Join meaningful lines
    meaningful_desc = '\n'.join(desc_lines[:30])  # Limit to first 30 meaningful lines

    # Extract timestamp chapters for better content structure
    timestamp_pattern = r'(\d{1,2}:\d{2})\s*[.\-]?\s*(.+)'
    timestamps = re.findall(timestamp_pattern, meaningful_desc)

    # Extract key features/benefits (usually marked with ✅ or similar)
    features = []
    for line in desc_lines:
        if '✅' in line or '核心' in line or '亮点' in line:
            features.append(line.replace('✅', '').strip())

    if features:
        content += "## 核心亮点\n\n"
        for feature in features[:6]:
            # Clean up the feature text
            feature = re.sub(r'[🚀💡✅🎯]', '', feature)
            feature = feature.replace('**', '').strip()
            if feature:
                content += f"**{feature}**\n\n"
        content += "\n"

    # Extract code examples if present
    code_blocks = re.findall(r'```[a-z]*\n(.*?)```', meaningful_desc, re.DOTALL)
    if code_blocks:
        content += "## 配置示例\n\n"
        for code in code_blocks[:2]:
            content += f"```\n{code.strip()}\n```\n\n"

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
        # Remove excessive emphasis
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold markdown
        line = re.sub(r'🚀\*\*', '', line)  # Remove rocket emoji

        # Simplify overly promotional language
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

    # If file exists, add timestamp
    if file_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_path = posts_path / f"{filename}-{timestamp}.md"
        print(f"File exists, creating with timestamp: {file_path.name}")

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

        # Auto deploy if enabled
        if args.deploy or config.get('auto_deploy', False):
            print("\n🚀 Auto-deploying to git...")
            deploy_branch = config.get('deploy_branch', 'main')
            deploy_to_git(blog_dir, deploy_branch)
        else:
            print(f"\n📂 To deploy: cd {blog_dir or '.'} && hexo cl; hexo g; hexo d")

    return 0


if __name__ == '__main__':
    sys.exit(main())
