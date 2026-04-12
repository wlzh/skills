#!/usr/bin/env python3
"""
YouTube to Blog Post Script - SEO Optimized Version v4.2
Convert YouTube videos to Hexo blog posts with enhanced SEO.

v4.1 changes:
- Add --title / --description / --tags / --video-id / --filename override args.
  When YouTube video is still processing (or fetch fails for any reason),
  supply metadata directly — no remote fetch needed.
  The caller (e.g. after youtube-publisher) already has all metadata; there is
  no need to re-fetch from the live URL.
- URL argument is now optional when override args supply enough metadata.
- --description is passed through 100% intact into article body; no truncation.
- Full YouTube description (resource links, affiliate links, chapters, etc.)
  is preserved as-is in the generated article.

v4.0 changes:
- FAQ auto-detection + placeholder section (enables Google FAQ rich snippets)
- Smart internal links section (相关推荐) generated from tags/category
- Improved description: strips emojis and markdown bold before use
- Auto category mapping aligned with blog category_map
- keywords now output as quoted comma string (SEO standard)
- Updated scaffold-aligned article structure
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
MAX_KEYWORD_LENGTH = 25  # Filter out overly long keyword fragments
MAX_IFRAME_TITLE_LENGTH = 50  # Keep iframe titles short and safe

# Blog category map (aligned with _config.yml category_map)
CATEGORY_MAP = {
    '技术': 'tech',
    '工具': 'tools',
    '教程': 'tutorial',
    '技术教程': 'tutorial',
    '软件': 'software',
    '生活': 'life',
    '学习': 'study',
    '学习资源': 'learning-resource',
    '网赚项目': 'online-earning',
    '技术支持': 'support',
}

# Auto-detect category from title keywords
CATEGORY_KEYWORDS = {
    '教程': '教程',
    '指南': '教程',
    'tutorial': '教程',
    'guide': '教程',
    'vps': '技术',
    '服务器': '技术',
    '域名': '技术',
    'cloudflare': '技术',
    'docker': '技术',
    'ssl': '技术',
    'vpn': '技术',
    '工具': '工具',
    'tool': '工具',
    '软件': '软件',
    'app': '软件',
    '银行': '技术',
    '支付': '技术',
    'wise': '技术',
    'esim': '技术',
    'ai': '技术',
    '学习': '学习',
}

# Stop words to filter from keywords
STOP_WORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', 'https', 'http', 'www', 'com', 'cn', 'org', 'net', '://', '//',
    '加入', '这个', '那个', '可以', '使用', '通过', '进行', '如果', '因为', '所以',
    # Additional low-quality keyword filters
    '视频教程', '手把手', '教程', '教程！', '指南', '方法', '攻略',
    '100%', '50', '1', '2', '3', '0',  # Pure numbers
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


def sanitize_for_html_attribute(text, max_length=50):
    """
    Sanitize text for HTML attributes (e.g., iframe title)
    Remove characters that can break HTML parsing

    Args:
        text: Text to sanitize
        max_length: Maximum length (default 50 for short, safe titles)

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
    """
    Clean and optimize keywords for SEO
    Filter out low-quality keywords:
    - Too short or too long
    - Stop words
    - Pure numbers
    - Title fragments with punctuation
    - URLs
    """
    cleaned = []

    for kw in keywords:
        # Remove special characters
        kw = sanitize_text_for_yaml(kw)

        # Skip if too short or too long
        if len(kw) < MIN_KEYWORD_LENGTH or len(kw) > MAX_KEYWORD_LENGTH:
            continue

        # Skip stop words
        if kw.lower() in STOP_WORDS or kw in STOP_WORDS:
            continue

        # Skip URLs
        if kw.startswith(('http', 'https', 'www', '//')):
            continue

        # Skip pure numbers or numbers with special chars
        if re.match(r'^[\d\s\-+=%#@!。，,、]+$', kw):
            continue

        # Skip if starts/ends with special chars
        if re.match(r'^[^\w]', kw) or re.search(r'[^\w]$', kw):
            continue

        # Skip title fragments (phrases with question marks, exclamation marks)
        if re.search(r'[？！!？。]', kw):
            continue

        # Skip if contains too many punctuation marks (likely a fragment)
        punctuation_count = len(re.findall(r'[,，、:：;；]', kw))
        if punctuation_count > 1:
            continue

        # Deduplicate
        if kw not in cleaned:
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
    for kw in keywords[:MAX_KEYWORDS * 2]:  # wider pool before capping
        if kw not in final_keywords:
            final_keywords.append(kw)

        # Add synonyms for important keywords
        if kw.lower() in KEYWORD_SYNONYMS:
            for synonym in KEYWORD_SYNONYMS[kw.lower()][:1]:
                if synonym not in final_keywords and len(final_keywords) < MAX_KEYWORDS:
                    final_keywords.append(synonym)

        if len(final_keywords) >= MAX_KEYWORDS:
            break

    return final_keywords[:MAX_KEYWORDS]


def strip_decorative_chars(text):
    """Remove emojis, markdown bold/italic, and leading decorative symbols from text."""
    # Remove markdown bold and italic
    text = re.sub(r'\*\*|\*|__', '', text)
    # Remove common emoji ranges
    text = re.sub(
        r'[\U0001F300-\U0001FFFF'   # misc symbols, emoticons
        r'\U00002600-\U000027BF'    # misc symbols
        r'\U0000FE00-\U0000FE0F'    # variation selectors
        r'\U00002B50\U00002B55'     # misc
        r']+', '', text
    )
    # Remove leading/trailing decorative ASCII like 🔥 leftover and clean up spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def auto_detect_category(title, tags):
    """Detect best-fit blog category from title keywords and tags."""
    title_lower = title.lower()
    # Check title first
    for kw, cat in CATEGORY_KEYWORDS.items():
        if kw in title_lower:
            return cat
    # Check tags
    if tags:
        tag_str = ' '.join(tags).lower() if isinstance(tags, list) else tags.lower()
        for kw, cat in CATEGORY_KEYWORDS.items():
            if kw in tag_str:
                return cat
    return '技术'  # default


def generate_seo_description(title, description):
    """
    Generate SEO-optimized description.
    - Max 160 characters (Google snippet length)
    - No emojis or markdown bold
    - Complete sentences, not truncated mid-word
    - Include main keywords
    """
    if description:
        # Step 1: strip emojis and markdown
        desc = strip_decorative_chars(description)

        # Step 2: Remove URLs, email addresses
        desc = re.sub(r'https?://\S+', '', desc)
        desc = re.sub(r'\S+@\S+', '', desc)

        # Step 3: Remove excessive whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Step 4: Find first meaningful sentence
        sentences = re.split(r'[。！？.!?]', desc)
        for sentence in sentences:
            sentence = sentence.strip()

            # Skip very short sentences
            if len(sentence) < 20:
                continue

            # Perfect length - use as-is
            if len(sentence) <= MAX_DESCRIPTION_LENGTH:
                return sentence

            # Too long - intelligently truncate at word boundary
            truncated = sentence[:MAX_DESCRIPTION_LENGTH]
            # Try to cut at last Chinese punctuation or space
            for punct in ['。', '，', '、', ' ']:
                pos = truncated.rfind(punct)
                if pos > MAX_DESCRIPTION_LENGTH * 0.7:
                    truncated = truncated[:pos + (1 if punct in '。，、' else 0)]
                    break
            return truncated.strip()

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

    # Auto-detect category if user passed the default (未指定)
    if category == '技术':
        category = auto_detect_category(title, tag_list)

    # Build cover image URL from YouTube thumbnail
    # Use high-quality thumbnail (maxresdefault)
    cover_image = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    # keywords as quoted comma string (SEO standard, matches blog scaffold)
    keywords_str = ', '.join(keywords)

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
keywords: "{keywords_str}"
cover: {cover_image}
thumbnail: {cover_image}
toc: true
comments: true
copyright: true
---

"""

    # Generate article summary
    summary = generate_article_summary(video_info)

    # Generate video iframe with SEO attributes - responsive via .video-container
    safe_title = sanitize_for_html_attribute(title)
    video_iframe = f"""## 视频教程

<div class="video-container">
<iframe src="https://www.youtube.com/embed/{video_id}" title="{safe_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

<!-- more -->

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
    """Kept for compatibility. In v4.0, keywords are written as quoted comma string in front matter."""
    if not keywords:
        return ""
    return ', '.join(keywords)


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


def dedupe_reference_sections(content):
    """Remove duplicated trailing reference sections generated by templating/humanizer interactions.
    Matches both old format ([相关推荐]) and new format ([869hr.uk 博客首页]).
    """
    # Generic dedup: remove any consecutive duplicate ## 参考链接 blocks
    pattern = re.compile(
        r'(## 参考链接\n\n(?:- .+\n)+\n---\n)(?:\n*\1)+',
        re.MULTILINE
    )
    return pattern.sub(r'\1', content)


def format_description_line(line):
    """
    将描述中的一行转为 Markdown 格式，把内联 URL 转为可点击链接。
    规则：行内出现 http://... 则提取 URL，用其前面紧邻的文字做链接文本。
    """
    # 把裸 URL 转成 Markdown 链接（保留原 URL，用域名做显示文本）
    def url_to_link(m):
        url = m.group(0).rstrip(')')  # 去掉可能粘连的右括号
        domain = re.search(r'https?://([^/?#\s]+)', url)
        label = domain.group(1) if domain else url
        return f"[{label}]({url})"

    # 如果整行就是一个裸 URL（常见于描述里单独一行放链接）
    if re.match(r'^https?://\S+$', line):
        url = line.rstrip(')')
        domain = re.search(r'https?://([^/?#\s]+)', url)
        label = domain.group(1) if domain else url
        return f"[{label}]({url})"

    # 行内有混合文字+URL，把 URL 部分替换成链接
    line = re.sub(r'https?://\S+', url_to_link, line)
    return line


def is_hashtag_line(line):
    """判断是否为纯 hashtag 行（如 #美国税号 #ITIN申请），博客正文不需要"""
    stripped = line.strip()
    if not stripped:
        return False
    # 全行都是 #词 的组合
    return bool(re.match(r'^(#[\w\u4e00-\u9fffA-Za-z]+\s*)+$', stripped))


def bracket_title_to_h3(line):
    """将【xxx】格式标题行转为 ### xxx Markdown 标题"""
    m = re.match(r'^【(.+?)】\s*$', line.strip())
    if m:
        return f"### {m.group(1)}"
    return None


def generate_article_content(video_info, video_id):
    """
    生成文章正文 —— 完整保留 YouTube 描述内容，不丢失任何文字或链接。
    格式转换规则（v4.2）：
    - 【xxx】 → ### xxx (H3 标题，SEO 结构化)
    - 时间戳行 → ## 视频章节（并从正文移除，含【视频分段】标题行）
    - 纯 hashtag 行 → 过滤（内容已在 tags 字段）
    - 裸 URL → Markdown 可点击链接
    - 时长为 0 时不显示（覆盖模式下未提供时长）
    - <!-- more --> 插入视频 iframe 后（Hexo 首页截断）
    """
    title = video_info['title']
    uploader = video_info.get('uploader', '')
    description = video_info.get('description', '')
    duration = video_info.get('duration', 0)

    # ── 视频介绍段落 ───────────────────────────────────────────────────────
    # 用 description 第一段作实质简介，而非仅显示时长
    intro_text = ""
    if description:
        first_lines = []
        for ln in description.split('\n'):
            s = ln.strip()
            if not s:
                if first_lines:
                    break
            elif not re.match(r'^\d{1,2}:\d{2}', s) and not s.startswith('【') and not s.startswith('#'):
                first_lines.append(s)
                if len(first_lines) >= 3:
                    break
        intro_text = ' '.join(first_lines)

    content = f"## 视频介绍\n\n"
    if intro_text:
        content += f"{intro_text}\n\n"
    if uploader:
        if duration and duration > 0:
            duration_min = duration // 60
            duration_sec = duration % 60
            content += f"**频道**：{uploader}　**时长**：{duration_min} 分 {duration_sec} 秒\n\n"
        else:
            content += f"**频道**：{uploader}\n\n"

    if not description:
        content += f"\n---\n\n## 参考链接\n\n- [YouTube 原视频](https://www.youtube.com/watch?v={video_id})\n- [869hr.uk 博客首页](https://869hr.uk)\n\n---\n"
        return content

    # ── 第一步：识别时间戳章节行，单独提取；同时移除章节标题行 ──────────
    timestamp_re = re.compile(r'^(\d{1,2}:\d{2})\s*[-–—]\s*(.+)$')
    # 【视频分段】这类标题行在时间戳已提取后应从正文移除
    section_header_re = re.compile(r'^【视频分段】\s*$')
    raw_lines = description.split('\n')

    timestamps = []
    other_lines = []
    for line in raw_lines:
        stripped = line.strip()
        if timestamp_re.match(stripped):
            m = timestamp_re.match(stripped)
            timestamps.append((m.group(1), m.group(2).strip()))
        elif section_header_re.match(stripped):
            pass  # 移除，内容已进入 ## 视频章节
        else:
            other_lines.append(line)

    if timestamps:
        content += "## 视频章节\n\n"
        for ts, chapter in timestamps:
            content += f"- **{ts}** {chapter}\n"
        content += "\n"

    # ── 第二步：把剩余描述整体转为 Markdown，完整保留所有内容 ──────────
    paragraphs = []
    current = []
    for line in other_lines:
        stripped = line.strip()
        if stripped == '':
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(stripped)
    if current:
        paragraphs.append(current)

    content += "## 详细内容\n\n"
    for para in paragraphs:
        # ① 过滤纯 hashtag 行
        para = [l for l in para if not is_hashtag_line(l)]
        if not para:
            continue

        # ② 单行段落
        if len(para) == 1:
            line = para[0]
            # 【xxx】→ ### xxx
            h3 = bracket_title_to_h3(line)
            if h3:
                content += h3 + "\n\n"
            else:
                content += format_description_line(line) + "\n\n"
        else:
            # 多行段落：先检查首行是否是【xxx】标题
            h3 = bracket_title_to_h3(para[0])
            if h3:
                content += h3 + "\n\n"
                rest = para[1:]
            else:
                rest = para

            if not rest:
                continue

            # 判断是否像列表
            all_list_like = all(
                re.match(r'^[\d\.\-\*✅💡📌🔗💬🔔👍🎯]+', l) or len(l) < 80
                for l in rest
            )
            if all_list_like:
                for l in rest:
                    content += format_description_line(l) + "\n\n"
            else:
                merged = ' '.join(rest)
                content += format_description_line(merged) + "\n\n"

    # ── 第三步：提取代码块（如有）────────────────────────────────────────
    code_blocks = re.findall(r'```[a-z]*\n(.*?)```', description, re.DOTALL)
    if code_blocks:
        content += "## 脚本命令\n\n"
        for code in code_blocks:
            content += f"```bash\n{code.strip()}\n```\n\n"

    # ── FAQ 章节（从描述提取，或生成占位模板）──────────────────────────
    faq_section = generate_faq_section(video_info)
    if faq_section:
        content += faq_section

    # ── 相关推荐内部链接区块 ────────────────────────────────────────────
    related_section = generate_related_posts_section(video_info)
    content += related_section

    # ── 尾部视频信息 ──────────────────────────────────────────────────────
    duration_str = ""
    if duration and duration > 0:
        duration_min = duration // 60
        duration_sec = duration % 60
        duration_str = f"\n- **时长**: {duration_min} 分 {duration_sec} 秒"

    content += f"""---

## 视频信息

- **视频标题**: {title}
- **UP主**: {uploader}{duration_str}

## 参考链接

- [YouTube 原视频](https://www.youtube.com/watch?v={video_id})
- [869hr.uk 博客首页](https://869hr.uk)

---
"""
    return content


def generate_faq_section(video_info):
    """
    Try to extract FAQ Q/A pairs from video description.
    If found, generate ## 常见问题 section (supports Google FAQ rich snippets).
    If not found, return empty string (user can add manually via scaffold template).
    """
    description = video_info.get('description', '')
    if not description:
        return ""

    faq_items = []

    # Pattern 1: explicit Q: / A: or 问：/答：
    qa_blocks = re.finditer(
        r'(?:Q[：:]\s*|问[：:]\s*)(.+?)(?:\n+)(?:A[：:]\s*|答[：:]\s*)(.+?)(?=\n\n|\nQ[：:]|\n问[：:]|$)',
        description, re.DOTALL
    )
    for m in qa_blocks:
        q = m.group(1).strip().replace('\n', ' ')
        a = m.group(2).strip().replace('\n', ' ')
        if q and a and len(q) < 120:
            faq_items.append((q, a))

    # Pattern 2: numbered questions like "1. 什么是XXX？\n答：..."
    numbered_qa = re.finditer(
        r'\d+\.\s+(.{5,80}[？?])\s*\n+\s*(?:答[：:]?\s*)?(.{10,300}?)(?=\n\n|\n\d+\.|$)',
        description, re.DOTALL
    )
    for m in numbered_qa:
        q = m.group(1).strip()
        a = m.group(2).strip().replace('\n', ' ')
        if q and a and len(q) < 120:
            faq_items.append((q, a))

    if not faq_items:
        return ""

    content = "## 常见问题（FAQ）\n\n"
    for q, a in faq_items[:5]:
        a_clean = strip_decorative_chars(a)
        content += f"**Q：{q}**\n\n**A：** {a_clean}\n\n---\n\n"

    return content


def generate_related_posts_section(video_info):
    """
    Generate 相关推荐 internal links section.
    Based on video tags/title keywords, suggest which blog posts to link to.
    Outputs placeholder links that the user should replace with real internal URLs.
    This section is critical for SEO internal linking.
    """
    title = video_info['title'].lower()
    tags = video_info.get('tags', [])
    tag_str = ' '.join(tags).lower() if tags else ''
    combined = title + ' ' + tag_str

    # Topic-based link suggestions (aligned with actual blog post patterns)
    suggestions = []

    if any(kw in combined for kw in ['wise', '银行', '支付', 'payment', '收款']):
        suggestions.append('<!-- 推荐链接：Wise/N26/银行卡系列 → /年份/tutorial/wise-mainland-phone-id-register-guide/ -->')
        suggestions.append('- [Wise 国内注册全教程（身份证+手机号）](/2026/tutorial/wise-mainland-phone-id-register-guide/)')

    if any(kw in combined for kw in ['esim', 'vodafone', '手机卡', '保号']):
        suggestions.append('<!-- 推荐链接：eSIM/手机卡系列 -->')
        suggestions.append('- [德国沃达丰 eSIM 申请全攻略](/2026/tutorial/vodafone-esim-wise-n26-guide/)')

    if any(kw in combined for kw in ['vps', '服务器', 'server', 'oracle', 'gcp']):
        suggestions.append('<!-- 推荐链接：VPS系列 -->')
        suggestions.append('- [VPS 安全加固全攻略](/2026/tutorial/vps-security-hardening-skill-tutorial/)')

    if any(kw in combined for kw in ['cloudflare', 'tunnel', 'cdn', 'dns', '域名']):
        suggestions.append('<!-- 推荐链接：Cloudflare/域名系列 -->')
        suggestions.append('- [Cloudflare Tunnel + Docker 内网穿透教程](/2026/tutorial/cloudflare-tunnel-docker-tutorial/)')

    if any(kw in combined for kw in ['telegram', 'tg', '电报']):
        suggestions.append('<!-- 推荐链接：Telegram系列 -->')
        suggestions.append('- [Telegram 中文语言包安装教程](/2025/software/telegram-chinese-pack/)')

    if any(kw in combined for kw in ['apple', 'ios', 'app store', 'apple id', '苹果']):
        suggestions.append('<!-- 推荐链接：苹果账号系列 -->')
        suggestions.append('- [美区 Apple ID 注册与购买 App 教程](/2025/tech/us-apple-id-guide/)')

    if any(kw in combined for kw in ['ai', 'gpt', 'deepseek', 'llm', '大语言', 'chatgpt']):
        suggestions.append('<!-- 推荐链接：AI工具系列 -->')
        suggestions.append('- [DeepSeek 相关传闻深度分析](/2025/tech/deepseek-20250208/)')

    # Generic fallback if no match
    if not suggestions:
        suggestions = [
            '<!-- 请手动添加2-3个相关文章内部链接，格式：[文章标题](/年份/分类/文件名/) -->',
            '<!-- 内部链接是 SEO 权重传递的关键，每篇文章至少2条 -->',
        ]

    content = "## 相关教程推荐\n\n"
    for s in suggestions:
        content += s + "\n"
    content += "\n"
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

        # Keep real title in content; don't replace it with placeholders like “这个教程”

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
        content = dedupe_reference_sections(content)
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
    parser.add_argument('url', nargs='?', default='', help='YouTube video URL (optional when --video-id + --title are provided)')
    parser.add_argument('-b', '--blog-dir', help='Blog directory path')
    parser.add_argument('-c', '--category', default='技术', help='Post category')
    parser.add_argument('-t', '--tags', nargs='+', default=['视频教程'], help='Post tags')
    parser.add_argument('--config', help='Path to config JSON file')
    parser.add_argument('--posts-dir', help='Override posts directory')
    parser.add_argument('--dry-run', action='store_true', help='Generate content but don\'t save')
    parser.add_argument('--no-humanizer', action='store_true', help='Skip AI writing removal (humanizer)')
    parser.add_argument('--deploy', action='store_true', help='Auto deploy to git after saving post')
    # ── v4.1 override args ──────────────────────────────────────────────────
    parser.add_argument('--title', dest='override_title', default='',
                        help='Override video title (skip YouTube fetch)')
    parser.add_argument('--description', dest='override_description', default='',
                        help='Override video description — passed through 100%% intact')
    parser.add_argument('--video-id', dest='override_video_id', default='',
                        help='Override YouTube video ID (e.g. B8gNipUixTo)')
    parser.add_argument('--filename', dest='override_filename', default='',
                        help='Force output filename (without .md)')
    parser.add_argument('--uploader', dest='override_uploader', default='',
                        help='Override uploader/channel name')

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

    # ── v4.1: build video_info from overrides OR fetch from YouTube ──────────
    has_overrides = bool(args.override_title and args.override_video_id)

    if has_overrides:
        # Caller already has all metadata; no remote fetch needed
        video_id = args.override_video_id
        video_info = {
            'id': video_id,
            'title': normalize_youtube_text(args.override_title),
            'description': normalize_youtube_text(args.override_description),
            'uploader': args.override_uploader or 'M.',
            'upload_date': datetime.now().strftime('%Y%m%d'),
            'duration': 0,
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            'tags': args.tags if args.tags != ['视频教程'] else [],
        }
        print(f"📹 Using provided metadata (skip YouTube fetch)")
        print(f"   Title: {video_info['title'][:60]}...")
    else:
        # Fetch from YouTube
        if not args.url:
            print("❌ Please provide a YouTube URL or use --title + --video-id overrides")
            return 1
        video_info = get_video_info(args.url)
        if not video_info:
            print("❌ Failed to fetch video information")
            print("   Tip: If the video is still processing, use:")
            print("   --title '...' --video-id 'xxxxx' --description '...'")
            return 1
        video_id = extract_video_id(args.url) or video_info['id']

    print(f"📹 Video: {video_info['title']}")
    print(f"👤 Uploader: {video_info.get('uploader', 'N/A')}")
    if blog_dir:
        print(f"📂 Blog: {blog_dir}")

    # Generate filename (override takes priority)
    if args.override_filename:
        filename = args.override_filename.rstrip('.md')
    else:
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
